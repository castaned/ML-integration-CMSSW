"""Recreate poster figures from saved scores; never retrain the model."""
import argparse
import csv
import json
from pathlib import Path
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score, roc_curve
import yaml

COLORS = {"DYJets": "#3266a8", "WZ": "#e79724", "ZZ": "#219578", "Wprime": "#cc375f"}


def load_scores(config):
    folder = Path(config["data"]["output_path"]).expanduser()
    name = config["model"]["name"]
    metrics = json.loads((folder / f"metrics_{name}.json").read_text())
    with (folder / f"scores_{name}.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    groups = {}
    for row in rows:
        sample = "Wprime" if row["sample"] == "signal_example" else row["sample"].removesuffix("_test")
        groups.setdefault(sample, []).append(float(row["anomaly_score"]))
    groups = {name: np.asarray(values) for name, values in groups.items()}
    if set(groups) != set(COLORS):
        raise ValueError(f"Expected DYJets/WZ/ZZ/Wprime; found {sorted(groups)}")
    if any(not len(v) or not np.isfinite(v).all() or np.any(v < 0) for v in groups.values()):
        raise ValueError("Invalid reconstruction scores")
    expected = metrics["normal_test_by_id"]
    for pid, process in metrics["normal_process_names"].items():
        if len(groups[process]) != expected[pid]:
            raise ValueError(f"Score count mismatch: {process}")
    if len(groups["Wprime"]) != metrics["signal_test"]:
        raise ValueError("Signal count mismatch")
    normal = np.concatenate([groups[p] for p in ("DYJets", "WZ", "ZZ")])
    weights = np.concatenate([np.full(len(groups[p]), 1 / (3 * len(groups[p])))
                              for p in ("DYJets", "WZ", "ZZ")])
    scores = np.concatenate([normal, groups["Wprime"]])
    labels = np.concatenate([np.zeros(len(normal)), np.ones(len(groups["Wprime"]))])
    weights = np.concatenate([weights, np.full(len(groups["Wprime"]), 1 / len(groups["Wprime"]))])
    auc = roc_auc_score(labels, scores, sample_weight=weights)
    if not np.isclose(auc, metrics["roc_auc"], atol=1e-6):
        raise ValueError("Saved scores do not reproduce reported AUC")
    return folder, name, metrics, groups, labels, scores, weights


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-f", "--file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    config = yaml.safe_load(args.file.read_text())
    folder, name, metrics, groups, labels, scores, weights = load_scores(config)
    output = args.output_dir or folder / "poster_figures_10variables"
    if output.exists():
        parser.error(f"Refusing to overwrite {output}; choose a new --output-dir")
    output.mkdir(parents=True)
    plt.rcParams.update({"font.size": 13, "axes.spines.top": False, "axes.spines.right": False})
    def save(stem):
        plt.tight_layout()
        plt.savefig(output / f"{stem}.pdf", bbox_inches="tight")
        plt.savefig(output / f"{stem}.png", dpi=300, bbox_inches="tight")
        plt.close()

    plt.figure(figsize=(7, 5.5))
    fpr, tpr, _ = roc_curve(labels, scores, sample_weight=weights)
    plt.plot(fpr, tpr, linewidth=2, label=f"{len(config['data']['features'])} variables: AUC {roc_auc_score(labels, scores, sample_weight=weights):.3f}")
    plt.plot([0, 1], [0, 1], "k--", linewidth=1)
    plt.xlabel("Aceptación de fondo SM (pesos iguales por proceso)")
    plt.ylabel("Eficiencia Wprime")
    plt.legend()
    save("ROC")

    precision, recall, _ = precision_recall_curve(labels, scores, sample_weight=weights)
    plt.figure(figsize=(7, 5.5))
    plt.plot(recall, precision, linewidth=2, label=f"AP {average_precision_score(labels, scores, sample_weight=weights):.3f}")
    plt.xlabel("Recobrado Wprime")
    plt.ylabel("Precisión (mezcla artificial SM:señal = 1:1)")
    plt.legend()
    save("PR")

    edges = np.linspace(0, scores.max() * 1.001 if scores.max() else 1, 51)
    threshold = metrics["threshold"]
    for separate in (False, True):
        plt.figure(figsize=(8, 5.5))
        if separate:
            for process, values in groups.items():
                plt.hist(values, bins=edges, weights=np.full(len(values), 1 / len(values)),
                         histtype="step", linewidth=1.8, color=COLORS[process], label=process)
        else:
            n = len(scores) - len(groups["Wprime"])
            plt.hist(scores[:n], bins=edges, weights=weights[:n], histtype="step", linewidth=2, label="SM (pesos iguales por proceso)")
            plt.hist(groups["Wprime"], bins=edges, weights=weights[n:], histtype="step", linewidth=2, color=COLORS["Wprime"], label="Wprime")
        plt.axvline(threshold, color="black", linestyle="--", label=f"Umbral de validación: {threshold:.2f}")
        plt.yscale("log")
        plt.xlabel("Error cuadrático medio de reconstrucción")
        plt.ylabel("Fracción ponderada por bin")
        plt.legend(fontsize=10)
        save("scores_by_process" if separate else "scores")

    widths = [len(config["data"]["features"])] + config["model"]["hidden_dims"] + [config["model"]["latent_dim"]] + list(reversed(config["model"]["hidden_dims"])) + [len(config["data"]["features"])]
    fig, ax = plt.subplots(figsize=(10, 2.8))
    for i, width in enumerate(widths):
        ax.text(i, 0, str(width), ha="center", va="center", fontsize=20,
                bbox={"boxstyle": "round,pad=0.6", "facecolor": "#d9e7f5" if i != 3 else "#ffe1a6"})
        if i:
            ax.annotate("", xy=(i - 0.28, 0), xytext=(i - 0.72, 0), arrowprops={"arrowstyle": "->"})
    for x, text in ((1, "Encoder"), (3, "Espacio latente"), (5, "Decoder")):
        ax.text(x, 0.65, text, ha="center")
    ax.set(xlim=(-0.6, 6.6), ylim=(-0.65, 1))
    ax.axis("off")
    save("architecture")

    loss = folder / f"loss_{name}.pdf"
    if loss.exists():
        shutil.copy2(loss, output / "loss.pdf")
    (output / "README.txt").write_text(
        "Exploratory HT70-100 DY pilot. Equal SM process weights, not luminosity weights.\n"
        "PR assumes total SM and signal weight 1:1; not physical purity.\n"
        "Loss PDF copied from actual training; epoch history is not reconstructed.\n"
        "AUC verified against saved metrics. Wprime used for evaluation only.\n", encoding="utf-8")
    print(f"Figures saved to {output}")


if __name__ == "__main__":
    main()
