"""Create a student's CMS configuration from the instructor's verified reference."""
import argparse
import copy
import os
from pathlib import Path
import yaml


def generate(source, output, results):
    source, output = Path(source).expanduser().resolve(), Path(output).expanduser().resolve()
    if output.exists() or Path(results).expanduser().exists():
        raise FileExistsError('Choose new personal config and result locations')
    config = copy.deepcopy(yaml.safe_load(source.read_text()))
    config['data']['output_path'] = str(Path(results).expanduser().resolve())
    for key in ('normal_input_paths', 'anomaly_input_paths'):
        paths = config['data'][key]
        if not paths:
            raise ValueError(f'Missing {key}')
        expanded = [str(Path(os.path.expandvars(p)).expanduser().resolve()) for p in paths]
        # Absolute input paths must be shared instructor paths, not student HOME aliases.
        if any(not Path(p).exists() for p in expanded):
            raise FileNotFoundError(f'Inputs not accessible: {expanded}')
        config['data'][key] = expanded
    config['model']['name'] = 'workshop_autoencoder'
    config['model']['export_onnx'] = False
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(config, sort_keys=False))
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference', required=True)
    p.add_argument('--config', required=True)
    p.add_argument('--results', required=True)
    a = p.parse_args()
    generate(a.reference, a.config, a.results)
