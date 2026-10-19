"""Create connected personal CMS NanoAOD, HDF5 and autoencoder YAMLs."""
import argparse
import json
from pathlib import Path

import yaml

TEMPLATES = Path(__file__).resolve().parent / 'configs'
PROCESSES = {'DYJets': ('DYjets', 4), 'WZ': ('WZ', 5),
             'ZZ': ('ZZ', 6), 'Wprime': ('Wprime', 1)}


def generate(inputs, workspace, tag='baseline01'):
    if not tag or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in tag):
        raise ValueError('Use letters, digits, underscores or hyphens for --tag')
    inputs, workspace = Path(inputs).resolve(), Path(workspace).resolve()
    configs = workspace / 'configs'
    paths = {kind: configs / f'cms_{kind}_{tag}.yaml'
             for kind in ('processing', 'root2h5', 'autoencoder')}
    root = workspace / 'cms' / tag / 'root'
    h5 = workspace / 'cms' / tag / 'h5'
    results = workspace / 'results' / f'cms_autoencoder_{tag}'
    manifest_path = configs / f'cms_inputs_{tag}.json'
    for path in [*paths.values(), manifest_path, root.parent, results]:
        if path.exists():
            raise FileExistsError(f'Use a new --tag; preserving {path}')
    manifest = {}
    for name, (folder, _) in PROCESSES.items():
        files = sorted((inputs / folder).rglob('*.root'))
        if not files:
            raise FileNotFoundError(f'No NanoAOD ROOT files under {inputs / folder}')
        if len({p.name for p in files}) != len(files):
            raise ValueError(f'Duplicate ROOT basenames in {name}; use a unique input set')
        if any(any(c.isspace() for c in str(p)) or ',' in str(p) for p in files):
            raise ValueError('Input paths must not contain whitespace or commas')
        manifest[name] = [str(p) for p in files]
    values = {kind: yaml.safe_load((TEMPLATES / f'cms_{kind}.yaml').read_text())
              for kind in paths}
    processing = values['processing']['data_processing']
    processing['datasets'] = [{'name': name, 'ID': info[1], 'files': manifest[name]}
                              for name, info in PROCESSES.items()]
    processing['eos_output_dir'] = str(root)
    conversion = values['root2h5']['convertion']
    conversion['input_dirs'] = [str(root / name) for name in PROCESSES]
    conversion['eos_output_dir'] = str(h5)
    data = values['autoencoder']['data']
    data['normal_input_paths'] = [str(h5 / name) for name in ('DYJets', 'WZ', 'ZZ')]
    data['anomaly_input_paths'] = [str(h5 / 'Wprime')]
    data['output_path'] = str(results)
    configs.mkdir(parents=True, exist_ok=True)
    for kind, path in paths.items():
        with path.open('x', encoding='utf-8') as handle:
            yaml.safe_dump(values[kind], handle, sort_keys=False)
        print(path)
    with manifest_path.open('x', encoding='utf-8') as handle:
        json.dump(manifest, handle, indent=2)
    print(f'Input manifest: {manifest_path}')
    print('Selected ROOT files:', {name: len(files) for name, files in manifest.items()})
    return paths


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path,
                        default=Path('/lustre/cursos/curso07/datos/autoencoder'))
    parser.add_argument('--workspace', type=Path, default=Path.home() / 'hep-workshop')
    parser.add_argument('--tag', default='baseline01')
    args = parser.parse_args()
    generate(args.inputs, args.workspace, args.tag)
