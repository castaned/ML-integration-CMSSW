"""Create separate Yuca configs for the three-lepton Z+W selected workflow."""

import argparse
import copy
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=Path.home() / "Open-Data")
    args = parser.parse_args()
    config_dir = args.config_dir.expanduser().resolve()
    sources = {
        "processing": config_dir / "data_processing_config.yaml",
        "qcd": config_dir / "qcd_data_processing_config.yaml",
        "conversion": config_dir / "root2h5_config.yaml",
        "autoencoder": config_dir / "autoencoder_sm_mixture_model_config.yaml",
    }
    targets = {
        "processing": config_dir / "wz_data_processing_config.yaml",
        "conversion": config_dir / "wz_root2h5_config.yaml",
        "autoencoder": config_dir / "autoencoder_sm_mixture_wz_model_config.yaml",
    }
    for path in sources.values():
        if not path.is_file():
            parser.error(f"Missing base configuration: {path}")
    for path in targets.values():
        if path.exists():
            parser.error(f"Refusing to overwrite existing configuration: {path}")

    configs = {}
    for key, path in sources.items():
        with path.open(encoding="utf-8") as handle:
            configs[key] = copy.deepcopy(yaml.safe_load(handle))

    processing = configs["processing"]["data_processing"]
    qcd_processing = configs["qcd"]["data_processing"]
    datasets = processing["datasets"] + qcd_processing["datasets"]
    expected = {"fondo": 2, "senal": 1, "QCD": 3}
    if {item["name"]: item["ID"] for item in datasets} != expected or len(datasets) != 3:
        parser.error("Expected exactly fondo=2, senal=1, and QCD=3 datasets")
    account = qcd_processing["slurm_params"].get("account")
    if not account:
        parser.error("Missing Slurm account in the QCD processing config")
    processing["datasets"] = datasets
    processing["slurm_params"]["account"] = account
    root_output = config_dir / "Processed" / "root_wz"
    h5_output = config_dir / "Processed" / "h5_wz"
    processing["eos_output_dir"] = str(root_output)

    conversion_config = configs["conversion"]
    conversion = conversion_config["convertion"]
    conversion["input_dirs"] = [str(root_output / name) for name in expected]
    conversion["eos_output_dir"] = str(h5_output)
    conversion_config["slurm_params"]["account"] = account

    autoencoder_config = configs["autoencoder"]
    data = autoencoder_config["data"]
    data["normal_input_paths"] = [str(h5_output / "fondo"), str(h5_output / "QCD")]
    data["anomaly_input_paths"] = [str(h5_output / "senal")]
    data["output_path"] = str(config_dir / "Processed" / "results_autoencoder_sm_mixture_wz")
    autoencoder_config["model"]["name"] = "autoencoder_sm_mixture_wz"

    for key, path in targets.items():
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(configs[key], handle, sort_keys=False, allow_unicode=True)
        print(path)


if __name__ == "__main__":
    main()
