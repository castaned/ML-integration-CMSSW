"""One Slurm array task per NanoAOD, followed by an afterok merge."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import yaml

REPO = Path(__file__).resolve().parents[1]


def submit(config_path, output, account, qos=None, env=None):
    config_path = Path(config_path).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    if output.exists():
        raise FileExistsError(output)
    config = yaml.safe_load(config_path.read_text())
    tasks, seen = [], set()
    for sample in config['samples']:
        for filename in sample['files']:
            path = Path(filename).expanduser().resolve()
            if not path.is_file():
                raise FileNotFoundError(path)
            if path in seen:
                raise ValueError('Duplicate NanoAOD input')
            seen.add(path)
            single = copy.deepcopy(config)
            single['samples'] = [dict(sample, files=[str(path)])]
            tasks.append(single)
    if not tasks:
        raise ValueError('No NanoAOD inputs')
    parts = output.with_name(output.name + '.parts')
    parts.mkdir(parents=True, exist_ok=False)
    (parts/'logs').mkdir()
    manifest = parts/'manifest.json'
    manifest.write_text(json.dumps({'config': config, 'tasks': tasks, 'output': str(output)}, indent=2))
    options = ['sbatch', '--parsable', f'--account={account}']
    if qos:
        options.append(f'--qos={qos}')
    resource = config.get('processing', {})
    options += [f'--time={resource.get("time", "01:00:00")}',
                f'--mem={resource.get("memory", "6G")}']
    script = str(REPO/'workshop/run_cpu.slurm')
    array = subprocess.check_output(options + [f'--array=1-{len(tasks)}',
        f'--output={parts}/logs/file_%A_%a.out', script, 'extract-file', str(manifest)],
        cwd=REPO, text=True, env=env).strip().split(';')[0]
    (parts/'submission.json').write_text(json.dumps({'array_job': array}, indent=2))
    print(f'NanoAOD processing: array {array}, {len(tasks)} tasks', flush=True)
    merge_job = subprocess.check_output(options + [f'--dependency=afterok:{array}',
        '--kill-on-invalid-dep=yes', f'--output={parts}/logs/merge_%j.out',
        script, 'merge-extraction', str(manifest)], cwd=REPO, text=True, env=env).strip().split(';')[0]
    (parts/'submission.json').write_text(json.dumps({'array_job': array, 'merge_job': merge_job}, indent=2))
    print(f'Merge/plots/HDF5: job {merge_job}, waiting for all tasks to succeed')
    return array, merge_job


def worker(manifest, index):
    from extract_fourleptons import extract
    path = Path(manifest)
    data = json.loads(path.read_text())
    if not 1 <= index <= len(data['tasks']):
        raise ValueError('Invalid array task index')
    extract(data['tasks'][index-1], path.parent/f'file_{index:05d}', allow_empty=True, plots=False)


def merge(manifest):
    import pandas as pd
    from event_io import read_events_h5
    from extract_fourleptons import save_results
    path = Path(manifest)
    data = json.loads(path.read_text())
    frames, flows, provenance = [], {}, []
    expected_map = {str(k): str(v) for k,v in data['config']['dataset_map'].items()}
    for index in range(1, len(data['tasks'])+1):
        folder = path.parent/f'file_{index:05d}'
        frame = read_events_h5(folder/'events.h5')
        if frame.attrs.get('dataset_map') != expected_map:
            raise ValueError(f'{folder}: inconsistent dataset map')
        if not frame.empty:
            frames.append(frame)
        for sample, counts in json.loads((folder/'cutflow.json').read_text()).items():
            target = flows.setdefault(sample, {})
            for stage, count in counts.items():
                target[stage] = target.get(stage, 0) + count
        provenance.extend(json.loads((folder/'provenance.json').read_text()))
    if not frames:
        raise ValueError('No selected events across all NanoAOD inputs; inspect per-file cutflows')
    combined = pd.concat(frames, ignore_index=True)
    if not combined.EventId.is_unique:
        raise ValueError('Duplicate event IDs across tasks')
    if Path(data['output']).exists():
        raise FileExistsError(data['output'])
    save_results(data['config'], data['output'], combined, flows, provenance)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='mode', required=True)
    s = sub.add_parser('submit')
    s.add_argument('-f', '--config', required=True)
    s.add_argument('--output', required=True)
    s.add_argument('--account', required=True)
    s.add_argument('--qos')
    w = sub.add_parser('worker'); w.add_argument('manifest')
    m = sub.add_parser('merge'); m.add_argument('manifest')
    a = p.parse_args()
    if a.mode == 'submit':
        submit(a.config, a.output, a.account, a.qos)
    elif a.mode == 'worker':
        worker(a.manifest, int(os.environ['SLURM_ARRAY_TASK_ID']))
    else:
        merge(a.manifest)
