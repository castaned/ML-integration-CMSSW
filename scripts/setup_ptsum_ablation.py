"""Add the selected three-lepton scalar pT sum to the no-cut SM pilot."""

import argparse
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=Path.home() / "Open-Data")
    args = parser.parse_args()
    config_dir = args.config_dir.expanduser().resolve()
    source = config_dir / "autoencoder_sm_cocktail_dy102_config.yaml"
    target = config_dir / "autoencoder_sm_cocktail_dy102_ptsum_config.yaml"
    if not source.is_file():
        parser.error(f"Missing base configuration: {source}")
    if target.exists():
        parser.error(f"Refusing to overwrite existing configuration: {target}")
    with source.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    baseline = ["MET_pt", "M3l", "Z_deltaR", "Z_mass"]
    if config["data"]["features"] != baseline:
        parser.error("Base configuration does not have the expected four features")
    config["data"]["features"] = baseline + ["Lep_pt_sum"]
    config["data"]["output_path"] = str(
        config_dir / "Processed/results_autoencoder_sm_cocktail_dy102_ptsum")
    config["model"]["name"] = "autoencoder_sm_cocktail_dy102_ptsum"
    with target.open("x", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)
    print(target)


if __name__ == "__main__":
    main()
