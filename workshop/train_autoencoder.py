"""Run existing CMS autoencoder with personal output and frozen config provenance."""
import argparse
import os
from pathlib import Path
import sys
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ml_training'))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('-f', '--config', required=True)
    a = p.parse_args()
    source = Path(a.config).expanduser()
    config = yaml.safe_load(source.read_text())
    out = Path(os.path.expandvars(config['data']['output_path'])).expanduser()
    if out.exists():
        raise FileExistsError('Use a new output_path for each experiment')
    from src.autoencoder import run_autoencoder
    out.mkdir(parents=True)
    (out / 'workshop_config.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
    run_autoencoder(config, str(out))
