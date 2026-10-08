"""Create QCD-only processing configs without overwriting the existing Yuca run."""

import argparse
import copy
from pathlib import Path

import yaml


def main():
    home = Path.home()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qcd-dir", type=Path, default=home / "Open-Data/Data/QCD")
    parser.add_argument("--config-dir", type=Path, default=home / "Open-Data")
    parser.add_argument("--qcd-id", type=int, default=3)
    args = parser.parse_args()

    qcd_dir = args.qcd_dir.expanduser().resolve()
    config_dir = args.config_dir.expanduser().resolve()
    if not qcd_dir.is_dir() or not list(qcd_dir.glob("*.root")):
        parser.error(f"No ROOT files found in {qcd_dir}")

    sources = {
        "processing": config_dir / "data_processing_config.yaml",
        "conversion": config_dir / "root2h5_config.yaml",
        "autoencoder": config_dir / "autoencoder_model_config.yaml",
    }
    targets = {
        "processing": config_dir / "qcd_data_processing_config.yaml",
        "conversion": config_dir / "qcd_root2h5_config.yaml",
        "autoencoder": config_dir / "autoencoder_qcd_model_config.yaml",
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
    processing["datasets"] = [{"name": "QCD", "ID": args.qcd_id, "path": str(qcd_dir)}]
    root_output = Path(processing["eos_output_dir"]).expanduser()

    conversion = configs["conversion"]["convertion"]
    conversion["input_dirs"] = [str(root_output / "QCD")]
    h5_output = Path(conversion["eos_output_dir"]).expanduser()

    autoencoder = configs["autoencoder"]["data"]
    autoencoder["qcd_input_paths"] = [str(h5_output / "QCD")]
    autoencoder["qcd_labels"] = [args.qcd_id]
    autoencoder["output_path"] = str(Path(autoencoder["output_path"]).expanduser()) + "_qcd"

    for key, path in targets.items():
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(configs[key], handle, sort_keys=False, allow_unicode=True)
        print(path)


if __name__ == "__main__":
    main()
