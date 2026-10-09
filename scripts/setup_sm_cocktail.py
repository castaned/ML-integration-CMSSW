"""Create isolated Yuca configs for an equal-process DYJets/WZ/ZZ pilot."""

import argparse
import copy
from pathlib import Path

import yaml


PROCESSES = {"DYJets": 4, "WZ": 5, "ZZ": 6}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=Path.home() / "Open-Data")
    parser.add_argument("--account", default="p002", help="Slurm project account")
    args = parser.parse_args()
    config_dir = args.config_dir.expanduser().resolve()
    data_dir = config_dir / "Data"
    for name in PROCESSES:
        path = data_dir / name
        if not path.is_dir() or not list(path.glob("*.root")):
            parser.error(f"No ROOT files found in {path}")

    sources = {
        "processing": config_dir / "wz_data_processing_config.yaml",
        "conversion": config_dir / "wz_ewk_root2h5_config.yaml",
        "autoencoder": config_dir / "autoencoder_ewk_wz_model_config.yaml",
    }
    targets = {
        "processing": config_dir / "sm_cocktail_processing_config.yaml",
        "conversion": config_dir / "sm_cocktail_root2h5_config.yaml",
        "autoencoder": config_dir / "autoencoder_sm_cocktail_model_config.yaml",
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
    processing["datasets"] = [
        {"name": name, "ID": process_id, "path": str(data_dir / name)}
        for name, process_id in PROCESSES.items()
    ]
    processing["slurm_params"]["account"] = args.account
    root_output = config_dir / "Processed" / "root_sm_cocktail"
    h5_output = config_dir / "Processed" / "h5_sm_cocktail"
    processing["eos_output_dir"] = str(root_output)

    conversion = configs["conversion"]
    conversion["slurm_params"]["account"] = args.account
    conversion["convertion"]["input_dirs"] = [str(root_output / name) for name in PROCESSES]
    conversion["convertion"]["eos_output_dir"] = str(h5_output)
    conversion["convertion"]["skip_empty_trees"] = True

    autoencoder = configs["autoencoder"]
    model_data = autoencoder["data"]
    model_data["normal_input_paths"] = [str(h5_output / name) for name in PROCESSES]
    model_data["normal_labels"] = list(PROCESSES.values())
    model_data["normal_process_names"] = {process_id: name for name, process_id in PROCESSES.items()}
    model_data["anomaly_input_paths"] = [str(config_dir / "Processed/h5_wz/senal")]
    model_data["anomaly_labels"] = [1]
    model_data.pop("qcd_input_paths", None)
    model_data.pop("qcd_labels", None)
    model_data["output_path"] = str(config_dir / "Processed/results_autoencoder_sm_cocktail")
    autoencoder["model"]["name"] = "autoencoder_sm_cocktail"

    for key, path in targets.items():
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(configs[key], handle, sort_keys=False, allow_unicode=True)
        print(path)


if __name__ == "__main__":
    main()
