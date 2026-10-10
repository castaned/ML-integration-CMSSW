"""Compare raw training observables by SM process with evaluation-only Wprime."""
import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ml_training"))
from src.autoencoder import _load_events, _split_by_process

LABELS = {"MET_pt": "MET [GeV]", "M3l": "M(3 leptones cargados) [GeV]",
          "Z_deltaR": "Delta R del par Z", "Z_mass": "M del par Z [GeV]",
          "Lep_pt_sum": "Suma escalar pT de 3 leptones [GeV]",
          "Z_pt": "pT del par Z [GeV]", "Lep1Z_pt": "pT lepton 1 del Z [GeV]",
          "Lep2Z_pt": "pT lepton 2 del Z [GeV]", "Lep3W_pt": "pT tercer lepton [GeV]",
          "W_mt": "M transversal lepton-MET [GeV]"}
COLORS = {"DYJets": "#3266a8", "WZ": "#e79724", "ZZ": "#219578", "Wprime": "#cc375f"}


def draw(ax, feature, index, groups):
    values = np.concatenate([array[:, index] for array in groups.values()])
    low, high = float(values.min()), float(values.max())
    if high == low:
        low, high = low - 0.5, high + 0.5
    bins = np.linspace(low, high, 41)
    for process, array in groups.items():
        ax.hist(array[:, index], bins=bins, density=True, histtype="step",
                linewidth=1.7, color=COLORS[process], label=f"{process} (n={len(array)})")
    ax.set_xlabel(LABELS.get(feature, feature))
    ax.set_ylabel("Densidad normalizada")
    ax.set_title(feature)
    ax.legend(fontsize=8)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-f", "--file", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.file.read_text())
    data, detection = config["data"], config["anomaly_detection"]
    features = data["features"]
    normal, ids = _load_events(data["normal_input_paths"], features, data["label"],
                               data["normal_labels"], return_labels=True)
    (train, _, _), (train_ids, _, _) = _split_by_process(normal, ids,
        detection["validation_fraction"], detection["test_fraction"], detection["seed"])
    signal = _load_events(data["anomaly_input_paths"], features, data["label"], data["anomaly_labels"])
    groups = {data["normal_process_names"][int(pid)]: train[train_ids == pid] for pid in sorted(np.unique(train_ids))}
    groups["Wprime"] = signal
    if set(groups) != set(COLORS) or any(not len(a) for a in groups.values()):
        raise ValueError("All four samples must be present and nonempty")
    metrics = json.loads((Path(data["output_path"]).expanduser() /
        f"metrics_{config['model']['name']}.json").read_text())
    for pid, process in data["normal_process_names"].items():
        if len(groups[process]) != metrics["normal_training_by_id"][str(pid)]:
            raise ValueError(f"Training count differs from saved run: {process}")
    if len(signal) != metrics["signal_test"]:
        raise ValueError("Wprime count differs from saved run")
    output = Path(data["output_path"]).expanduser() / "poster_figures_10variables/variable_distributions"
    if output.exists():
        parser.error(f"Refusing to overwrite {output}")
    output.mkdir(parents=True)
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    def save(fig, stem):
        fig.savefig(output / f"{stem}.pdf", bbox_inches="tight")
        fig.savefig(output / f"{stem}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)
    rows = (len(features) + 1) // 2
    fig, axes = plt.subplots(rows, 2, figsize=(12, rows * 3.2), constrained_layout=True, squeeze=False)
    for index, feature in enumerate(features):
        draw(axes.flat[index], feature, index, groups)
    for ax in list(axes.flat)[len(features):]:
        ax.axis("off")
    fig.suptitle("Observables originales: entrenamiento SM y evaluacion Wprime", fontsize=15)
    save(fig, "variables_all")
    selected = [f for f in ("MET_pt", "M3l", "Z_pt", "W_mt") if f in features]
    if len(selected) == 4:
        fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
        for ax, feature in zip(axes.flat, selected):
            draw(ax, feature, features.index(feature), groups)
        save(fig, "variables_selected")
    for index, feature in enumerate(features):
        fig, ax = plt.subplots(figsize=(7, 4.8), constrained_layout=True)
        draw(ax, feature, index, groups)
        save(fig, f"variable_{feature}")
    (output / "sample_counts.json").write_text(json.dumps({
        "SM_role": "training only, seeded per-process split",
        "Wprime_role": "evaluation only, not used to fit model or preprocessing",
        "normalization": "unit area per process; no luminosity weighting",
        "values": "raw observables before standardization; full range, common bins",
        "features": features, "counts": {name: len(a) for name, a in groups.items()}}, indent=2))
    print(f"Variable figures saved to {output}")
