"""Plot Wprime event scores from an existing run; no retraining required."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument("--name", default="cms_autoencoder")
    args = parser.parse_args()
    folder = args.results.expanduser()
    threshold = float(json.loads((folder / f"metrics_{args.name}.json").read_text())["threshold"])
    with (folder / f"scores_{args.name}.csv").open(newline="", encoding="utf-8") as stream:
        scores = np.array([float(row["anomaly_score"]) for row in csv.DictReader(stream)
                           if row["sample"] == "signal_example"])
    if not len(scores):
        raise ValueError("No Wprime evaluation scores found")
    selected = scores >= threshold
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout=True)
    indices = np.arange(len(scores))
    ax.scatter(indices[~selected], scores[~selected], s=8, alpha=.45,
               color="tab:blue", label="Bajo el umbral")
    ax.scatter(indices[selected], scores[selected], s=13, alpha=.75,
               color="crimson", label="Seleccionados")
    ax.axhline(threshold, color="black", linestyle="--", label=f"Umbral = {threshold:.3f}")
    ax.set(xlabel="Indice del evento", ylabel="Error de reconstruccion",
           title=f"Wprime: evaluacion | {len(scores)} eventos | {100*selected.mean():.2f}% seleccionados")
    ax.legend()
    for ext in ("png", "pdf", "svg"):
        target = folder / f"events_Wprime_{args.name}.{ext}"
        fig.savefig(target, dpi=180)
        print(target)
    plt.close(fig)


if __name__ == "__main__":
    main()
