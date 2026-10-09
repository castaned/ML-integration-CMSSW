"""Create separate HDF5 samples and autoencoder config for Z-pair DeltaR < 1.5."""

import argparse
from pathlib import Path

import h5py
import numpy as np
import yaml


MAX_DR = 1.5
SAMPLES = {
    "DYJets": "h5_sm_cocktail/DYJets",
    "WZ": "h5_sm_cocktail/WZ",
    "ZZ": "h5_sm_cocktail/ZZ",
    "senal": "h5_wz/senal",
}


def passing_dr(handle, path):
    n_events = len(handle["Dataset_ID"])
    passes = np.column_stack([handle[f"{channel}_pass"][:].astype(bool)
                              for channel in "ABCD"])
    if passes.shape != (n_events, 4) or np.any(passes.sum(axis=1) != 1):
        raise ValueError(f"{path}: expected exactly one passing channel per event")
    dr = np.empty(n_events, dtype=np.float32)
    for index, channel in enumerate("ABCD"):
        values = handle[f"{channel}_Dr_Z"][:]
        dr[passes[:, index]] = values[passes[:, index]]
    if not np.isfinite(dr).all():
        raise ValueError(f"{path}: non-finite Z-pair DeltaR")
    return dr < MAX_DR


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-dir", type=Path, default=Path.home() / "Open-Data")
    args = parser.parse_args()
    config_dir = args.config_dir.expanduser().resolve()
    source_config = config_dir / "autoencoder_sm_cocktail_boosted_config.yaml"
    target_config = config_dir / "autoencoder_sm_cocktail_dr15_config.yaml"
    source_root = config_dir / "Processed"
    target_root = source_root / "h5_sm_cocktail_dr15"
    if not source_config.is_file():
        parser.error(f"Missing base configuration: {source_config}")
    if target_config.exists() or target_root.exists():
        parser.error("Refusing to overwrite existing DeltaR-selected data or configuration")
    for name, relative in SAMPLES.items():
        if not list((source_root / relative).glob("*.h5")):
            parser.error(f"No HDF5 files in {source_root / relative}")

    with source_config.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    data = config["data"]
    data["normal_input_paths"] = [str(target_root / name)
                                  for name in ("DYJets", "WZ", "ZZ")]
    data["anomaly_input_paths"] = [str(target_root / "senal")]
    data["output_path"] = str(source_root / "results_autoencoder_sm_cocktail_dr15")
    config["model"]["name"] = "autoencoder_sm_cocktail_dr15"

    target_root.mkdir(parents=True)
    for name, relative in SAMPLES.items():
        target_dir = target_root / name
        target_dir.mkdir()
        total = kept = 0
        for path in sorted((source_root / relative).glob("*.h5")):
            with h5py.File(path, "r") as source:
                mask = passing_dr(source, path)
                total += len(mask)
                count = int(mask.sum())
                kept += count
                if not count:
                    continue
                with h5py.File(target_dir / path.name, "w") as target:
                    for key, node in source.items():
                        if not isinstance(node, h5py.Dataset) or node.shape[0] != len(mask):
                            raise ValueError(f"{path}: unsupported HDF5 node {key}")
                        target.create_dataset(key, data=node[mask], compression="gzip")
        if not kept:
            raise ValueError(f"{name}: no events pass Z-pair DeltaR < {MAX_DR}")
        print(f"{name}: {kept}/{total} events -> {target_dir}")

    with target_config.open("x", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)
    print(target_config)


if __name__ == "__main__":
    main()
