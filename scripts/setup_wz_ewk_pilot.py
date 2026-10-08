"""Create conversion and autoencoder configs for the selected EWK/Wprime pilot."""

import argparse
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=Path.home() / "Open-Data")
    args = parser.parse_args()
    config_dir = args.config_dir.expanduser().resolve()
    conversion_source = config_dir / "wz_root2h5_config.yaml"
    autoencoder_source = config_dir / "autoencoder_model_config.yaml"
    conversion_target = config_dir / "wz_ewk_root2h5_config.yaml"
    autoencoder_target = config_dir / "autoencoder_ewk_wz_model_config.yaml"
    for source in (conversion_source, autoencoder_source):
        if not source.is_file():
            parser.error(f"Missing base configuration: {source}")
    for target in (conversion_target, autoencoder_target):
        if target.exists():
            parser.error(f"Refusing to overwrite existing configuration: {target}")

    with conversion_source.open(encoding="utf-8") as handle:
        conversion = yaml.safe_load(handle)
    with autoencoder_source.open(encoding="utf-8") as handle:
        autoencoder = yaml.safe_load(handle)

    conv = conversion["convertion"]
    roots = {Path(raw).name: Path(raw) for raw in conv["input_dirs"]}
    if not {"fondo", "senal"}.issubset(roots):
        parser.error("The WZ conversion config must include fondo and senal")
    if (roots["fondo"].parent != roots["senal"].parent
            or roots["fondo"].parent.name != "root_wz"):
        parser.error("Expected fondo and senal under the selected root_wz directory")
    if not conversion["slurm_params"].get("account"):
        parser.error("The WZ conversion config needs a Slurm account")
    conv["input_dirs"] = [str(roots[name]) for name in ("fondo", "senal")]
    h5_output = Path(conv["eos_output_dir"])

    data = autoencoder["data"]
    data["normal_input_paths"] = [str(h5_output / "fondo")]
    data["anomaly_input_paths"] = [str(h5_output / "senal")]
    data.pop("qcd_input_paths", None)
    data.pop("qcd_labels", None)
    data["normal_labels"] = [2]
    data["anomaly_labels"] = [1]
    data["output_path"] = str(config_dir / "Processed" / "results_autoencoder_ewk_wz")
    autoencoder["model"]["name"] = "autoencoder_ewk_wz"

    for target, config in ((conversion_target, conversion),
                           (autoencoder_target, autoencoder)):
        with target.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)
        print(target)


if __name__ == "__main__":
    main()
