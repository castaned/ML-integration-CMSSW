"""Plot frozen-autoencoder anomaly score against three-lepton mass and channel."""

import argparse
import json
from pathlib import Path

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml

from compare_autoencoder_scores import process_weights, residuals
from models.models import AutoencoderModel
from src.autoencoder import _files, _load_events


COLORS = {4: "#2563a6", 5: "#e89827", 6: "#25956b", 1: "#c63353"}
NAMES = {4: "DYJets", 5: "WZ", 6: "ZZ", 1: "Wprime"}


def load_channels(paths):
    channels = []
    for path in _files(paths):
        with h5py.File(path) as handle:
            flags = np.column_stack([handle[f"{channel}_pass"][:].astype(bool)
                                     for channel in "ABCD"])
        if np.any(flags.sum(axis=1) != 1):
            raise ValueError(f"{path}: expected exactly one passing channel per event")
        channels.append(np.asarray(list("ABCD"))[np.argmax(flags, axis=1)])
    return np.concatenate(channels)


def test_indices(labels, validation_fraction, test_fraction, seed):
    selected = []
    for process_id in sorted(np.unique(labels)):
        group = np.flatnonzero(labels == process_id)
        shuffled = np.random.default_rng(seed + int(process_id)).permutation(len(group))
        n_val = round(len(group) * validation_fraction)
        n_test = round(len(group) * test_fraction)
        selected.extend(group[shuffled[n_val:n_val + n_test]])
    return np.asarray(selected, dtype=int)


def plot_scatter(ax, mass, scores, ids, threshold, title):
    for process_id in (4, 5, 6, 1):
        mask = ids == process_id
        if np.any(mask):
            ax.scatter(mass[mask], scores[mask], s=12, alpha=0.55,
                       color=COLORS[process_id], label=NAMES[process_id])
    ax.axhline(threshold, color="black", linestyle="--", linewidth=1.2,
               label="SM validation threshold")
    ax.set_yscale("log")
    ax.set_xlabel("M(3 charged leptons) [GeV]")
    ax.set_ylabel("Reconstruction MSE")
    ax.set_title(title)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-f", "--file", type=Path, required=True)
    args = parser.parse_args()
    with args.file.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    data = config["data"]
    settings = config["model"]
    detection = config["anomaly_detection"]
    features = list(data["features"])
    if "M3l" not in features:
        parser.error("The model must include the M3l feature")
    model_dir = Path(data["output_path"]).expanduser()
    output_dir = model_dir / "mass_channel_diagnostics"
    if output_dir.exists():
        parser.error(f"Refusing to overwrite existing results: {output_dir}")
    checkpoint = torch.load(model_dir / f"best_model_{settings['name']}.pth",
                            map_location="cpu", weights_only=True)
    if features != checkpoint["features"]:
        raise ValueError("Config features do not match the saved model")

    normal, normal_ids = _load_events(data["normal_input_paths"], features,
                                      data["label"], data["normal_labels"],
                                      return_labels=True)
    signal = _load_events(data["anomaly_input_paths"], features,
                          data["label"], data["anomaly_labels"])
    normal_channels = load_channels(data["normal_input_paths"])
    signal_channels = load_channels(data["anomaly_input_paths"])
    if len(normal_channels) != len(normal) or len(signal_channels) != len(signal):
        raise ValueError("Channel metadata does not align with model inputs")
    indices = test_indices(normal_ids, float(detection["validation_fraction"]),
                           float(detection["test_fraction"]), int(detection["seed"]))
    normal, normal_ids, normal_channels = (normal[indices], normal_ids[indices],
                                            normal_channels[indices])
    mean = np.asarray(checkpoint["mean"], dtype=np.float32)
    scale = np.asarray(checkpoint["scale"], dtype=np.float32)
    normalize = lambda values: np.asarray((values - mean) / scale, dtype=np.float32)
    model = AutoencoderModel(len(features), checkpoint["hidden_dims"],
                             checkpoint["latent_dim"])
    model.load_state_dict(checkpoint["model_state"])
    batch_size = int(settings["batch_size"])
    normal_scores = np.mean(residuals(model, normalize(normal), batch_size) ** 2, axis=1)
    signal_scores = np.mean(residuals(model, normalize(signal), batch_size) ** 2, axis=1)
    threshold = float(checkpoint["threshold"])
    metrics_path = model_dir / f"metrics_{settings['name']}.json"
    with metrics_path.open(encoding="utf-8") as handle:
        metrics = json.load(handle)
    if (len(normal) != metrics["normal_test"] or len(signal) != metrics["signal_test"]
            or not np.isclose(np.mean(normal_scores >= threshold),
                              metrics["normal_test_fpr"], atol=1e-8)):
        raise ValueError("The current HDF5 inputs differ from the saved training run")
    mass_index = features.index("M3l")
    mass = np.concatenate((normal[:, mass_index], signal[:, mass_index]))
    scores = np.concatenate((normal_scores, signal_scores))
    ids = np.concatenate((normal_ids, np.ones(len(signal), dtype=int)))
    channels = np.concatenate((normal_channels, signal_channels))

    report = {"threshold": threshold, "test_event_counts": {},
              "above_threshold_by_channel": {}}
    for process_id in (4, 5, 6, 1):
        mask = ids == process_id
        report["test_event_counts"][NAMES[process_id]] = int(mask.sum())
        report["above_threshold_by_channel"][NAMES[process_id]] = {
            channel: {"events": int(np.count_nonzero(mask & (channels == channel))),
                      "above_threshold": int(np.count_nonzero(
                          mask & (channels == channel) & (scores >= threshold)))}
            for channel in "ABCD"}

    output_dir.mkdir(parents=True)
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), constrained_layout=True)
    for ax, process_id in zip(axes.flat, (4, 5, 6, 1)):
        mask = ids == process_id
        plot_scatter(ax, mass[mask], scores[mask], ids[mask], threshold,
                     f"{NAMES[process_id]} ({mask.sum()} events)")
    fig.savefig(output_dir / "score_vs_m3l_by_process.pdf")
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9), constrained_layout=True)
    for ax, channel in zip(axes.flat, "ABCD"):
        mask = channels == channel
        plot_scatter(ax, mass[mask], scores[mask], ids[mask], threshold,
                     f"Channel {channel} ({mask.sum()} events)")
    axes.flat[0].legend(loc="upper right", fontsize=8)
    fig.savefig(output_dir / "score_vs_m3l_by_channel.pdf")
    plt.close(fig)

    bins = np.histogram_bin_edges(normal[:, mass_index], bins=35)
    weights = process_weights(normal_ids)
    plt.figure(figsize=(8, 5))
    plt.hist(normal[:, mass_index], bins=bins, weights=weights,
             histtype="step", linewidth=2, label="SM test, before score cut")
    plt.hist(normal[normal_scores >= threshold, mass_index], bins=bins,
             weights=weights[normal_scores >= threshold], histtype="step",
             linewidth=2, label="SM test, after score cut")
    plt.xlabel("M(3 charged leptons) [GeV]")
    plt.ylabel("Fraction of equal-process SM test sample / bin")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "sm_mass_before_after_score.pdf")
    plt.close()
    with (output_dir / "channel_counts.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))
    print(f"Results: {output_dir}")


if __name__ == "__main__":
    main()
