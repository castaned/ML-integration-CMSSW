import copy
import csv
import json
import os
from pathlib import Path

import h5py
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import onnx
import torch
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve, precision_recall_curve
from torch.utils.data import DataLoader, TensorDataset

from models.models import AutoencoderModel


def _files(paths):
    files = []
    for raw in paths:
        path = Path(os.path.expanduser(os.path.expandvars(raw)))
        if path.is_dir():
            files.extend(sorted(path.glob("*.h5")))
        elif path.is_file() and path.suffix == ".h5":
            files.append(path)
        else:
            raise FileNotFoundError(f"HDF5 path not found: {path}")
    if not files:
        raise ValueError("No HDF5 files found")
    return files


def _load_events(paths, features, label, allowed_labels):
    arrays = []
    allowed = set(int(value) for value in allowed_labels)
    for path in _files(paths):
        with h5py.File(path, "r") as handle:
            missing = set(features + [label]) - set(handle.keys())
            if missing:
                raise ValueError(f"{path}: missing branches {sorted(missing)}")
            labels = np.asarray(handle[label][:], dtype=int)
            if not set(np.unique(labels)).issubset(allowed):
                raise ValueError(f"{path}: contains labels outside {sorted(allowed)}")
            columns = []
            for feature in features:
                column = np.asarray(handle[feature][:], dtype=np.float32)
                if column.ndim != 1 or len(column) != len(labels):
                    raise ValueError(f"{path}: {feature} must be one scalar per event")
                columns.append(column)
            values = np.column_stack(columns)
            if not np.isfinite(values).all():
                raise ValueError(f"{path}: non-finite feature values")
            arrays.append(values)
    return np.concatenate(arrays)


def _split_normal(values, validation_fraction, test_fraction, seed):
    if not 0 < validation_fraction < 1 or not 0 < test_fraction < 1:
        raise ValueError("Validation and test fractions must be between 0 and 1")
    if validation_fraction + test_fraction >= 1:
        raise ValueError("Validation and test fractions must sum to less than 1")
    shuffled = np.random.default_rng(seed).permutation(len(values))
    n_val = round(len(values) * validation_fraction)
    n_test = round(len(values) * test_fraction)
    if min(n_val, n_test, len(values) - n_val - n_test) < 2:
        raise ValueError("Not enough normal events for train/validation/test")
    return values[shuffled[n_val + n_test:]], values[shuffled[:n_val]], values[shuffled[n_val:n_val + n_test]]


def _scores(model, values, device, batch_size):
    model.eval()
    result = []
    with torch.no_grad():
        for (batch,) in DataLoader(TensorDataset(torch.from_numpy(values)), batch_size=batch_size):
            batch = batch.to(device)
            reconstruction = model(batch)
            result.append(torch.mean((reconstruction - batch) ** 2, dim=1).cpu().numpy())
    return np.concatenate(result)


def _save_plots(history, val_scores, threshold, normal_scores, anomaly_scores,
                qcd_scores, labels, scores, output_dir, name):
    plt.figure(figsize=(7, 5))
    plt.plot(history["train_loss"], label="Training")
    plt.plot(history["val_loss"], label="SM validation")
    plt.xlabel("Epoch")
    plt.ylabel("Mean squared reconstruction error")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / f"loss_{name}.pdf")
    plt.close()

    plt.figure(figsize=(7, 5))
    plt.hist(normal_scores, bins=50, density=True, alpha=0.6, label="EWK test")
    if len(anomaly_scores):
        plt.hist(anomaly_scores, bins=50, density=True, alpha=0.6, label="Wprime example")
    if len(qcd_scores):
        plt.hist(qcd_scores, bins=50, density=True, alpha=0.5, label="QCD test")
    plt.axvline(threshold, color="crimson", linestyle="--", linewidth=2,
                label=f"Threshold = {threshold:.3f}")
    plt.yscale("log")
    plt.xlabel("Reconstruction error (anomaly score)")
    plt.ylabel("Density")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / f"scores_{name}.pdf")
    plt.close()

    if len(qcd_scores):
        plt.figure(figsize=(7, 5))
        plt.hist(normal_scores, bins=50, density=True, alpha=0.6, label="EWK test")
        plt.hist(qcd_scores, bins=50, density=True, alpha=0.6, label="QCD test")
        plt.axvline(threshold, color="crimson", linestyle="--", linewidth=2,
                    label=f"EWK threshold = {threshold:.3f}")
        plt.yscale("log")
        plt.xlabel("Reconstruction error (anomaly score)")
        plt.ylabel("Density")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / f"EWK_QCD_{name}.pdf")
        plt.close()

    below = val_scores < threshold
    indices = np.arange(len(val_scores))
    plt.figure(figsize=(9, 5))
    plt.scatter(indices[below], val_scores[below], s=12, color="tab:blue",
                alpha=0.7, label=f"Below threshold ({below.sum()})")
    plt.scatter(indices[~below], val_scores[~below], s=18, color="crimson",
                alpha=0.85, label=f"At or above threshold ({(~below).sum()})")
    plt.axhline(threshold, color="black", linestyle="--", linewidth=1.5,
                label=f"Threshold = {threshold:.3f}")
    plt.xlabel("Event index in SM validation sample")
    plt.ylabel("Reconstruction error (anomaly score)")
    plt.title("SM validation events and anomaly threshold")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / f"validation_events_{name}.pdf")
    plt.close()

    if len(anomaly_scores):
        fpr, tpr, _ = roc_curve(labels, scores)
        plt.figure(figsize=(7, 5))
        plt.plot(fpr, tpr, label=f"AUC = {roc_auc_score(labels, scores):.3f}")
        plt.plot([0, 1], [0, 1], "k--")
        plt.xlabel("False positive rate")
        plt.ylabel("True positive rate")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / f"ROC_{name}.pdf")
        plt.close()

        precision, recall, _ = precision_recall_curve(labels, scores)
        plt.figure(figsize=(7, 5))
        plt.plot(recall, precision, label=f"AP = {average_precision_score(labels, scores):.3f}")
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / f"PR_{name}.pdf")
        plt.close()


def run_autoencoder(config, output_path):
    data = config["data"]
    settings = config["model"]
    detection = config["anomaly_detection"]
    features = list(data["features"])
    if not features or len(set(features)) != len(features):
        raise ValueError("Features must be a nonempty list without duplicates")
    normal_labels = set(int(value) for value in data["normal_labels"])
    anomaly_labels = set(int(value) for value in data["anomaly_labels"])
    if not normal_labels or normal_labels & anomaly_labels:
        raise ValueError("Normal and anomaly labels must be nonempty and disjoint")

    qcd_paths = data.get("qcd_input_paths", [])
    qcd_labels = set(int(value) for value in data.get("qcd_labels", []))
    if qcd_paths and (not qcd_labels or qcd_labels & (normal_labels | anomaly_labels)):
        raise ValueError("QCD labels must be nonempty and distinct from normal and signal labels")

    normal = _load_events(data["normal_input_paths"], features, data["label"], normal_labels)
    anomaly_paths = data.get("anomaly_input_paths", [])
    anomaly = _load_events(anomaly_paths, features, data["label"], anomaly_labels) if anomaly_paths else np.empty((0, len(features)), dtype=np.float32)
    qcd = _load_events(qcd_paths, features, data["label"], qcd_labels) if qcd_paths else np.empty((0, len(features)), dtype=np.float32)
    if qcd_paths and not len(qcd):
        raise ValueError("QCD input contains no events; check the skim before evaluation")
    seed = int(detection.get("seed", 16))
    torch.manual_seed(seed)
    torch.set_num_threads(max(1, int(os.environ.get("SLURM_CPUS_PER_TASK", "1"))))
    train, val, test = _split_normal(normal, float(detection["validation_fraction"]), float(detection["test_fraction"]), seed)

    # Fit preprocessing on normal training events only.
    mean = train.mean(axis=0)
    scale = train.std(axis=0)
    scale[scale == 0] = 1
    normalize = lambda values: np.asarray((values - mean) / scale, dtype=np.float32)
    train, val, test, anomaly, qcd = map(normalize, (train, val, test, anomaly, qcd))

    hidden_dims = [int(width) for width in settings["hidden_dims"]]
    latent_dim = int(settings["latent_dim"])
    if not hidden_dims or min(hidden_dims + [latent_dim]) < 1 or latent_dim >= len(features):
        raise ValueError("Autoencoder needs positive hidden widths and a latent dimension smaller than the input")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AutoencoderModel(len(features), hidden_dims, latent_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(settings["learning_rate"]))
    batch_size = int(settings["batch_size"])
    patience = int(settings["patience"])
    if batch_size < 1 or patience < 1:
        raise ValueError("batch_size and patience must be positive")
    loader = DataLoader(TensorDataset(torch.from_numpy(train)), batch_size=batch_size, shuffle=True)
    val_tensor = torch.from_numpy(val).to(device)
    history = {"train_loss": [], "val_loss": []}
    best_loss = float("inf")
    best_state = None
    stale = 0
    for epoch in range(int(settings["epochs"])):
        model.train()
        losses = []
        for (batch,) in loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            loss = torch.mean((model(batch) - batch) ** 2)
            loss.backward()
            optimizer.step()
            losses.append((loss.item(), len(batch)))
        model.eval()
        with torch.no_grad():
            val_loss = torch.mean((model(val_tensor) - val_tensor) ** 2).item()
        train_loss = sum(loss * count for loss, count in losses) / len(train)
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        print(f"Epoch {epoch + 1}: train={train_loss:.6f}, SM validation={val_loss:.6f}")
        if val_loss < best_loss:
            best_loss = val_loss
            best_state = copy.deepcopy(model.state_dict())
            stale = 0
        else:
            stale += 1
            if stale >= patience:
                break
    if best_state is None:
        raise ValueError("epochs must be positive")
    model.load_state_dict(best_state)

    val_scores = _scores(model, val, device, batch_size)
    quantile = float(detection["normal_quantile"])
    if not 0 < quantile < 1:
        raise ValueError("normal_quantile must be between 0 and 1")
    threshold = float(np.quantile(val_scores, quantile))
    normal_scores = _scores(model, test, device, batch_size)
    anomaly_scores = _scores(model, anomaly, device, batch_size) if len(anomaly) else np.empty(0)
    qcd_scores = _scores(model, qcd, device, batch_size) if len(qcd) else np.empty(0)
    scores = np.concatenate((normal_scores, anomaly_scores))
    labels = np.concatenate((np.zeros(len(normal_scores), dtype=int), np.ones(len(anomaly_scores), dtype=int)))

    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    name = settings["name"]
    checkpoint = output_dir / f"best_model_{name}.pth"
    torch.save({"model_state": {key: value.cpu() for key, value in best_state.items()}, "features": features,
                "mean": mean.tolist(), "scale": scale.tolist(), "threshold": threshold,
                "hidden_dims": hidden_dims, "latent_dim": latent_dim}, checkpoint)
    if settings.get("export_onnx", True):
        model.cpu().eval()
        onnx_path = output_dir / f"best_model_{name}.onnx"
        torch.onnx.export(model, torch.zeros(1, len(features)), str(onnx_path), opset_version=18,
                          input_names=["input"], output_names=["reconstruction"],
                          dynamic_axes={"input": {0: "batch"}, "reconstruction": {0: "batch"}})
        onnx.checker.check_model(onnx.load(str(onnx_path)))

    _save_plots(history, val_scores, threshold, normal_scores, anomaly_scores,
                qcd_scores, labels, scores, output_dir, name)
    metrics = {"normal_train": len(train), "normal_validation": len(val), "normal_test": len(test),
               "signal_test": len(anomaly), "normal_quantile": quantile, "threshold": threshold,
               "normal_test_fpr": float(np.mean(normal_scores >= threshold)),
               "signal_test_tpr": float(np.mean(anomaly_scores >= threshold)) if len(anomaly_scores) else None,
               "qcd_test": len(qcd),
               "qcd_test_fpr": float(np.mean(qcd_scores >= threshold)) if len(qcd_scores) else None,
               "roc_auc": float(roc_auc_score(labels, scores)) if len(anomaly_scores) else None,
               "average_precision": float(average_precision_score(labels, scores)) if len(anomaly_scores) else None,
               "features": features, "seed": seed}
    with open(output_dir / f"metrics_{name}.json", "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    with open(output_dir / f"scores_{name}.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sample", "anomaly_score", "above_threshold"])
        for score, label in zip(scores, labels):
            writer.writerow(["signal_example" if label else "EWK_test", float(score), int(score >= threshold)])
        for score in qcd_scores:
            writer.writerow(["QCD_test", float(score), int(score >= threshold)])
    print(json.dumps(metrics, indent=2))
