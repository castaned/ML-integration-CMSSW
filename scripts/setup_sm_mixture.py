"""Create a separate EWK+QCD normal-training config from the QCD evaluation config."""

import argparse
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=Path.home() / "Open-Data")
    args = parser.parse_args()
    config_dir = args.config_dir.expanduser().resolve()
    source = config_dir / "autoencoder_qcd_model_config.yaml"
    target = config_dir / "autoencoder_sm_mixture_model_config.yaml"
    if not source.is_file():
        parser.error(f"Missing QCD evaluation config: {source}")
    if target.exists():
        parser.error(f"Refusing to overwrite existing configuration: {target}")

    with source.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    data = config["data"]
    qcd_paths = data.pop("qcd_input_paths", None)
    qcd_labels = data.pop("qcd_labels", None)
    if not qcd_paths or not qcd_labels:
        parser.error("QCD input paths and labels are required in the source config")
    data["normal_input_paths"] = list(data["normal_input_paths"]) + list(qcd_paths)
    data["normal_labels"] = list(data["normal_labels"]) + list(qcd_labels)
    if set(data["normal_labels"]) != {2, 3} or set(data["anomaly_labels"]) != {1}:
        parser.error("Expected EWK=2, QCD=3, Wprime=1 in the source config")
    data["output_path"] = str(Path(data["output_path"]).parent /
                              "results_autoencoder_sm_mixture")
    config["model"]["name"] = "autoencoder_sm_mixture"
    with target.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)
    print(target)


if __name__ == "__main__":
    main()
