"""Compare an equal-process SM density score with a frozen autoencoder."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml
from scipy.special import logsumexp
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.neighbors import KernelDensity

from compare_autoencoder_scores import process_weights, residuals
from models.models import AutoencoderModel
from src.autoencoder import _balanced_quantile, _load_events, _split_by_process


BANDWIDTHS = (0.3, 0.5, 0.8, 1.2, 1.8)


def fit_process_densities(train, ids, bandwidth):
    return {int(process_id): KernelDensity(bandwidth=bandwidth).fit(
        train[ids == process_id]) for process_id in np.unique(ids)}


def mixture_log_density(models, values):
    components = [model.score_samples(values) for model in models.values()]
    return logsumexp(np.stack(components), axis=0) - np.log(len(models))


def operating_points(val_scores, val_ids, test_scores, test_ids, signal_scores):
    result = {}
    for target_fpr in (0.01, 0.05):
        threshold = _balanced_quantile(val_scores, val_ids, 1 - target_fpr)
        by_process = {str(int(process_id)): float(np.mean(
            test_scores[test_ids == process_id] >= threshold))
            for process_id in sorted(np.unique(test_ids))}
        result[f"{target_fpr:.0%}"] = {
            "threshold_from_sm_validation": threshold,
            "balanced_sm_test_fpr": float(np.mean(list(by_process.values()))),
            "sm_test_fpr_by_id": by_process,
            "signal_test_tpr": float(np.mean(signal_scores >= threshold)),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-f", "--file", type=Path, required=True,
                        help="YAML configuration of the saved five-feature autoencoder")
    args = parser.parse_args()
    with args.file.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    data = config["data"]
    settings = config["model"]
    detection = config["anomaly_detection"]
    model_dir = Path(data["output_path"]).expanduser()
    output_dir = model_dir / "sm_density_study"
    if output_dir.exists():
        parser.error(f"Refusing to overwrite existing results: {output_dir}")
    checkpoint = torch.load(model_dir / f"best_model_{settings['name']}.pth",
                            map_location="cpu", weights_only=True)
    features = list(data["features"])
    if features != checkpoint["features"]:
        raise ValueError("Config features do not match the saved model")
    expected_ids = set(map(int, data["normal_labels"]))
    normal, ids = _load_events(data["normal_input_paths"], features, data["label"],
                               expected_ids, return_labels=True)
    if set(np.unique(ids)) != expected_ids:
        raise ValueError("Missing a configured SM process")
    signal = _load_events(data["anomaly_input_paths"], features,
                          data["label"], data["anomaly_labels"])
    (train, val, test), (train_ids, val_ids, test_ids) = _split_by_process(
        normal, ids, float(detection["validation_fraction"]),
        float(detection["test_fraction"]), int(detection["seed"]))
    mean = np.asarray(checkpoint["mean"], dtype=np.float32)
    scale = np.asarray(checkpoint["scale"], dtype=np.float32)
    normalize = lambda values: np.asarray((values - mean) / scale, dtype=np.float32)
    train, val, test, signal = map(normalize, (train, val, test, signal))

    bandwidth_quality = {}
    for bandwidth in BANDWIDTHS:
        models = fit_process_densities(train, train_ids, bandwidth)
        log_density = mixture_log_density(models, val)
        bandwidth_quality[bandwidth] = float(np.mean([
            log_density[val_ids == process_id].mean()
            for process_id in sorted(expected_ids)]))
    bandwidth = max(BANDWIDTHS, key=bandwidth_quality.get)
    models = fit_process_densities(train, train_ids, bandwidth)
    density_val = -mixture_log_density(models, val)
    density_test = -mixture_log_density(models, test)
    density_signal = -mixture_log_density(models, signal)

    model = AutoencoderModel(len(features), checkpoint["hidden_dims"],
                             checkpoint["latent_dim"])
    model.load_state_dict(checkpoint["model_state"])
    batch_size = int(settings["batch_size"])
    ae_val, ae_test, ae_signal = (
        np.mean(residuals(model, values, batch_size) ** 2, axis=1)
        for values in (val, test, signal))
    original_threshold = _balanced_quantile(
        ae_val, val_ids, float(detection["normal_quantile"]))
    if not np.isclose(original_threshold, checkpoint["threshold"],
                      rtol=1e-3, atol=1e-3):
        raise ValueError("The HDF5 inputs or split differ from the saved training run")

    labels = np.concatenate((np.zeros(len(test), dtype=int),
                             np.ones(len(signal), dtype=int)))
    weights = np.concatenate((process_weights(test_ids),
                              np.full(len(signal), 1 / len(signal))))
    report = {"features": features, "bandwidth_chosen_from_sm_validation": bandwidth,
              "sm_validation_log_density_by_bandwidth": {
                  str(key): value for key, value in bandwidth_quality.items()},
              "normal_test_by_id": {str(pid): int(np.count_nonzero(test_ids == pid))
                                    for pid in sorted(expected_ids)},
              "signal_test": len(signal), "methods": {}}
    plt.figure(figsize=(7, 5))
    for name, val_scores, test_scores, signal_scores in (
        ("SM density rarity", density_val, density_test, density_signal),
        ("Autoencoder MSE", ae_val, ae_test, ae_signal),
    ):
        scores = np.concatenate((test_scores, signal_scores))
        auc = float(roc_auc_score(labels, scores, sample_weight=weights))
        fpr, tpr, _ = roc_curve(labels, scores, sample_weight=weights)
        plt.plot(fpr, tpr, label=f"{name}: AUC {auc:.3f}")
        report["methods"][name] = {
            "roc_auc_equal_process_weights": auc,
            "operating_points": operating_points(val_scores, val_ids, test_scores,
                                                   test_ids, signal_scores),
        }
    plt.plot([0, 1], [0, 1], "k--", linewidth=1)
    plt.xlabel("SM false positive rate (equal process weights)")
    plt.ylabel("Wprime true positive rate (evaluation only)")
    plt.legend()
    plt.tight_layout()
    output_dir.mkdir(parents=True)
    plt.savefig(output_dir / "density_vs_autoencoder_roc.pdf")
    plt.close()
    with (output_dir / "density_comparison.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))
    print(f"Results: {output_dir}")


if __name__ == "__main__":
    main()
