"""Report the selected-sample efficiency of a Z-lepton DeltaR cut."""

import argparse
from pathlib import Path

import h5py
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path,
                        default=Path.home() / "Open-Data/Processed")
    parser.add_argument("--max-dr", type=float, default=1.5)
    args = parser.parse_args()
    if args.max_dr <= 0:
        parser.error("--max-dr must be positive")
    base = args.data_dir.expanduser().resolve()
    samples = {
        "DYJets": base / "h5_sm_cocktail/DYJets",
        "WZ": base / "h5_sm_cocktail/WZ",
        "ZZ": base / "h5_sm_cocktail/ZZ",
        "Wprime": base / "h5_wz/senal",
    }
    print(f"Z-pair DeltaR < {args.max_dr:g} (unweighted selected MC events)")
    for name, directory in samples.items():
        files = sorted(directory.glob("*.h5"))
        if not files:
            parser.error(f"No HDF5 files found in {directory}")
        total = kept = 0
        for path in files:
            with h5py.File(path) as handle:
                n_events = len(handle["Dataset_ID"])
                passes = np.column_stack([handle[f"{channel}_pass"][:].astype(bool)
                                          for channel in "ABCD"])
                if np.any(passes.sum(axis=1) != 1):
                    raise ValueError(f"{path}: expected exactly one passing channel")
                dr = np.empty(n_events, dtype=float)
                for index, channel in enumerate("ABCD"):
                    values = handle[f"{channel}_Dr_Z"][:]
                    dr[passes[:, index]] = values[passes[:, index]]
                total += n_events
                kept += int(np.count_nonzero(dr < args.max_dr))
        print(f"{name}: {kept}/{total} = {kept / total:.1%}")


if __name__ == "__main__":
    main()
