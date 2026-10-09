"""Compare reconstruction scores using a frozen SM-trained autoencoder."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml
from sklearn.metrics import roc_auc_score, roc_curve

from models.models import AutoencoderModel
from src.autoencoder import _balanced_quantile, _load_events, _split_by_process


def residuals(model, values, batch_size):
    chunks = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(values), batch_size):
            batch = torch.from_numpy(values[start:start + batch_size])
            chunks.append((model(batch) - batch).numpy())
    return np.concatenate(chunks)


def process_weights(ids):
    weights = np.zeros(len(ids), dtype=np.float64)
    processes = np.unique(ids)
    for process_id in processes:
        mask = ids == process_id
        weights[mask] = 1 / (len(processes) * mask.sum())
    return weights


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-f", "--file", type=Path, required=True,
                        help="Autoencoder YAML configuration used for training")
    parser.add_argument("--output-dir", type=Path,
                        help="Separate directory for the score comparison")
    args = parser.parse_args()
    with args.file.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    data = config["data"]
    settings = config["model"]
    detection = config["anomaly_detection"]
    model_dir = Path(data["output_path"]).expanduser()
    checkpoint_path = model_dir / f"best_model_{settings['name']}.pth"
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    features = list(data["features"])
    if features != checkpoint["features"]:
        raise ValueError("Config features do not match the saved model")
    output_dir = args.output_dir or model_dir / "score_study"
    if output_dir.exists():
        parser.error(f"Refusing to overwrite existing results: {output_dir}")

    normal_ids_expected = set(map(int, data["normal_labels"]))
    normal, normal_ids = _load_events(data["normal_input_paths"], features,
                                      data["label"], normal_ids_expected,
                                      return_labels=True)
    if set(np.unique(normal_ids)) != normal_ids_expected:
        raise ValueError("Missing a configured SM process")
    signal = _load_events(data["anomaly_input_paths"], features,
                          data["label"], data["anomaly_labels"])
    (train, validation, test), (train_ids, validation_ids, test_ids) = _split_by_process(
        normal, normal_ids, float(detection["validation_fraction"]),
        float(detection["test_fraction"]), int(detection["seed"]))
    mean = np.asarray(checkpoint["mean"], dtype=np.float32)
    scale = np.asarray(checkpoint["scale"], dtype=np.float32)
    normalize = lambda values: np.asarray((values - mean) / scale, dtype=np.float32)
    train, validation, test, signal = map(normalize,
                                          (train, validation, test, signal))
    model = AutoencoderModel(len(features), checkpoint["hidden_dims"],
                             checkpoint["latent_dim"])
    model.load_state_dict(checkpoint["model_state"])
    batch_size = int(settings["batch_size"])
    train_residuals, validation_residuals, test_residuals, signal_residuals = (
        residuals(model, values, batch_size)
        for values in (train, validation, test, signal))
    residual_scale = np.sqrt(np.mean([
        np.mean(train_residuals[train_ids == process_id].astype(np.float64) ** 2,
                axis=0)
        for process_id in sorted(normal_ids_expected)], axis=0))
    residual_scale = np.maximum(residual_scale, 1e-6)
    score_functions = {
        "mse": lambda errors: np.mean(errors ** 2, axis=1),
        "calibrated_mse": lambda errors: np.mean((errors / residual_scale) ** 2,
                                                  axis=1),
        "calibrated_max": lambda errors: np.max(np.abs(errors / residual_scale),
                                                 axis=1),
    }
    labels = np.concatenate((np.zeros(len(test), dtype=int),
                             np.ones(len(signal), dtype=int)))
    evaluation_weights = np.concatenate((process_weights(test_ids),
                                         np.full(len(signal), 1 / len(signal))))
    report = {"features": features, "normal_test_by_id": {
        str(pid): int(np.count_nonzero(test_ids == pid))
        for pid in sorted(normal_ids_expected)}, "signal_test": len(signal),
        "residual_scale_from_sm_train": dict(zip(features, residual_scale.tolist())),
        "scores": {}}
    plt.figure(figsize=(7, 5))
    for name, score_fn in score_functions.items():
        val_scores = score_fn(validation_residuals)
        if name == "mse":
            original_threshold = _balanced_quantile(
                val_scores, validation_ids, float(detection["normal_quantile"]))
            if not np.isclose(original_threshold, checkpoint["threshold"],
                              rtol=1e-3, atol=1e-3):
                raise ValueError("The HDF5 inputs or split differ from the saved training run")
        test_scores = score_fn(test_residuals)
        signal_scores = score_fn(signal_residuals)
        combined = np.concatenate((test_scores, signal_scores))
        auc = float(roc_auc_score(labels, combined,
                                  sample_weight=evaluation_weights))
        fpr, tpr, _ = roc_curve(labels, combined,
                                sample_weight=evaluation_weights)
        plt.plot(fpr, tpr, label=f"{name}: AUC {auc:.3f}")
        operating_points = {}
        for target_fpr in (0.01, 0.05):
            threshold = _balanced_quantile(val_scores, validation_ids,
                                           1 - target_fpr)
            operating_points[f"{target_fpr:.0%}"] = {
                "threshold_from_sm_validation": threshold,
                "balanced_sm_test_fpr": float(np.mean([
                    np.mean(test_scores[test_ids == pid] >= threshold)
                    for pid in sorted(normal_ids_expected)])),
                "sm_test_fpr_by_id": {str(pid): float(np.mean(
                    test_scores[test_ids == pid] >= threshold))
                    for pid in sorted(normal_ids_expected)},
                "signal_test_tpr": float(np.mean(signal_scores >= threshold)),
            }
        report["scores"][name] = {"roc_auc_equal_process_weights": auc,
                                   "operating_points": operating_points}
    plt.plot([0, 1], [0, 1], "k--", linewidth=1)
    plt.xlabel("SM false positive rate (equal process weights)")
    plt.ylabel("Wprime true positive rate (evaluation only)")
    plt.legend()
    plt.tight_layout()
    output_dir.mkdir(parents=True)
    plt.savefig(output_dir / "score_roc_comparison.pdf")
    plt.close()
    with (output_dir / "score_comparison.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(json.dumps(report, indent=2))
    print(f"Results: {output_dir}")


if __name__ == "__main__":
    main()
