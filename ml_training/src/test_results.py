# Test the model
import json
import torch
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, confusion_matrix, ConfusionMatrixDisplay
import models.models as models
from sklearn.preprocessing import label_binarize
import numpy as np
from itertools import cycle
from torch.utils.data import DataLoader


def compute_ROC(outputs, labels, num_classes, output_dir, model_name, class_labels=None):
    if class_labels is None:
        class_labels = {i: f"Label {i}" for i in range(num_classes)}

    if num_classes == 2:  # Binary
        probabilities = torch.softmax(torch.tensor(outputs, dtype=torch.float32), dim=1)[:, 1].numpy()
        fpr, tpr, _ = roc_curve(labels, probabilities)
        roc_auc = auc(fpr, tpr)

        label_name = class_labels.get(1, "Label 1")
        plt.plot(fpr, tpr, lw=2, label=f"{label_name} AUC = {roc_auc:.2f}")
    else:  # Multiclass
        probabilities = torch.softmax(torch.tensor(outputs, dtype=torch.float32), dim=1).numpy()
        n_classes = probabilities.shape[1]

        y_bin = label_binarize(labels, classes=np.arange(n_classes))

        fpr, tpr, roc_auc = dict(), dict(), dict()
        colors = cycle(["blue", "red", "green", "purple", "orange"])

        for i, color in zip(range(n_classes), colors):
            fpr[i], tpr[i], _ = roc_curve(y_bin[:, i], probabilities[:, i])
            roc_auc[i] = auc(fpr[i], tpr[i])

            label_name = class_labels.get(i, f"Label {i}")
            plt.plot(fpr[i], tpr[i], color=color, lw=2, label=f"{label_name} (AUC = {roc_auc[i]:.2f})")

    plt.plot([0, 1], [0, 1], "k--", lw=2)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend(loc="lower right")
    plt.grid(True)

    plt.savefig(f"{output_dir}/ROC_{model_name}.png")
    plt.savefig(f"{output_dir}/ROC_{model_name}.pdf")
    plt.close()

    return 0


def compute_cm(outputs, labels, output_dir, model_name, class_labels=None):
    predictions = np.argmax(outputs, axis=1)

    cm = confusion_matrix(labels, predictions)

    if isinstance(class_labels, dict):
        label_names = [class_labels.get(i, str(i)) for i in range(len(class_labels))]
    else:
        label_names = [str(i) for i in range(cm.shape[0])]

    n_classes = len(label_names)
    plt.figure(figsize=(max(8, n_classes * 0.8), max(6, n_classes * 0.7)))

    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=label_names)
    disp.plot(cmap="Blues", values_format="d", xticks_rotation=45 if n_classes > 2 else 0)

    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/cm_{model_name}.png", dpi=200, bbox_inches="tight")
    plt.savefig(f"{output_dir}/cm_{model_name}.pdf", dpi=200, bbox_inches="tight")
    plt.close()

    return 0


def test_results(model_name, model_type, dataset, output_dir, batch_size=2048, class_labels=None):
    param_model = torch.load(f"{output_dir}/best_model_{model_name}.pth", weights_only=True)

    if model_type == "mlp":
        model = models.MLPmodel.get_model(dataset.num_features, dataset.num_classes, param_model)
    print(model)

    dataloader = DataLoader(dataset, batch_size=batch_size)

    all_outputs = []
    all_labels = []

    model.eval()
    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            outputs = model(X_batch)

            all_outputs.append(outputs.cpu().numpy())
            all_labels.append(y_batch.cpu().numpy())

    outputs_test = np.concatenate(all_outputs)
    labels_test = np.concatenate(all_labels)

    compute_ROC(outputs_test, labels_test, dataset.num_classes, output_dir, model_name, class_labels)
    compute_cm(outputs_test, labels_test, output_dir, model_name, class_labels)

    dataset.close()
    return 0


def _binary_labels(labels, anomaly_labels):
    anomaly_labels = set(int(label) for label in anomaly_labels)
    return np.asarray([1 if int(label) in anomaly_labels else 0 for label in labels], dtype=int)


def _reconstruction_errors(model, dataset, batch_size):
    dataloader = DataLoader(dataset, batch_size=batch_size)
    all_errors = []
    all_labels = []

    model.eval()
    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            reconstruction = model(X_batch)
            errors = torch.mean((reconstruction - X_batch) ** 2, dim=1)
            all_errors.append(errors.cpu().numpy())
            all_labels.append(y_batch.cpu().numpy())

    return np.concatenate(all_errors), np.concatenate(all_labels)


def _plot_reconstruction_hist(scores, binary_labels, output_dir, model_name, split_name):
    normal_scores = scores[binary_labels == 0]
    anomaly_scores = scores[binary_labels == 1]

    plt.figure(figsize=(8, 5))
    plt.hist(normal_scores, bins=50, alpha=0.7, density=True, label="normal")
    plt.hist(anomaly_scores, bins=50, alpha=0.7, density=True, label="anomaly")
    plt.xlabel("Reconstruction error")
    plt.ylabel("Density")
    plt.title(f"Reconstruction Error ({split_name})")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/reconstruction_error_{split_name}_{model_name}.png", dpi=180)
    plt.savefig(f"{output_dir}/reconstruction_error_{split_name}_{model_name}.pdf")
    plt.close()


def _plot_reconstruction_events(scores, binary_labels, output_dir, model_name, split_name, threshold=None, max_events=300):
    if scores.size == 0:
        return

    limit = min(int(max_events), scores.size)
    event_ids = np.arange(limit)
    visible_scores = scores[:limit]
    visible_labels = binary_labels[:limit]

    normal_mask = visible_labels == 0
    anomaly_mask = visible_labels == 1

    plt.figure(figsize=(10, 5))
    plt.plot(event_ids, visible_scores, color="0.7", linestyle="--", linewidth=1, alpha=0.8)
    plt.scatter(event_ids[normal_mask], visible_scores[normal_mask], s=20, color="tab:blue", label="normal")
    plt.scatter(event_ids[anomaly_mask], visible_scores[anomaly_mask], s=28, color="tab:red", label="anomaly")

    if threshold is not None:
        plt.axhline(threshold, color="black", linestyle=":", linewidth=1.5, label=f"threshold = {threshold:.4g}")

    plt.xlabel(f"Event index (first {limit} events)")
    plt.ylabel("Reconstruction error")
    plt.title(f"Reconstruction Error by Event ({split_name})")
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/reconstruction_error_events_{split_name}_{model_name}.png", dpi=180)
    plt.savefig(f"{output_dir}/reconstruction_error_events_{split_name}_{model_name}.pdf")
    plt.close()


def _plot_binary_roc(scores, binary_labels, output_dir, model_name):
    fpr, tpr, _ = roc_curve(binary_labels, scores)
    roc_auc = auc(fpr, tpr)

    plt.figure(figsize=(7, 5))
    plt.plot(fpr, tpr, lw=2, label=f"AUC = {roc_auc:.3f}")
    plt.plot([0, 1], [0, 1], "k--", lw=1)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Autoencoder ROC Curve")
    plt.grid(True, alpha=0.25)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/ROC_{model_name}.png", dpi=180)
    plt.savefig(f"{output_dir}/ROC_{model_name}.pdf")
    plt.close()
    return roc_auc


def _plot_binary_pr(scores, binary_labels, output_dir, model_name):
    precision, recall, _ = precision_recall_curve(binary_labels, scores)
    pr_auc = auc(recall, precision)

    plt.figure(figsize=(7, 5))
    plt.plot(recall, precision, lw=2, label=f"PR AUC = {pr_auc:.3f}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Autoencoder Precision-Recall Curve")
    plt.grid(True, alpha=0.25)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/PR_{model_name}.png", dpi=180)
    plt.savefig(f"{output_dir}/PR_{model_name}.pdf")
    plt.close()
    return pr_auc


def _best_f1_threshold(scores, binary_labels):
    precision, recall, thresholds = precision_recall_curve(binary_labels, scores)
    if thresholds.size == 0:
        return float(np.mean(scores)) if scores.size else 0.0

    f1_scores = 2 * precision[:-1] * recall[:-1] / np.clip(precision[:-1] + recall[:-1], 1e-12, None)
    best_idx = int(np.nanargmax(f1_scores))
    return float(thresholds[best_idx])


def _plot_binary_confusion(scores, binary_labels, threshold, output_dir, model_name):
    predictions = (scores >= threshold).astype(int)
    cm = confusion_matrix(binary_labels, predictions)

    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["normal", "anomaly"])
    disp.plot(cmap="Blues", values_format="d")
    plt.title(f"Confusion Matrix (threshold={threshold:.4f})")
    plt.tight_layout()
    plt.savefig(f"{output_dir}/cm_{model_name}.png", dpi=180, bbox_inches="tight")
    plt.savefig(f"{output_dir}/cm_{model_name}.pdf", bbox_inches="tight")
    plt.close()

    tn, fp, fn, tp = cm.ravel()
    return {
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "tpr": float(tp / max(tp + fn, 1)),
        "fpr": float(fp / max(fp + tn, 1)),
        "precision": float(tp / max(tp + fp, 1)),
        "accuracy": float((tp + tn) / max(cm.sum(), 1)),
    }


def test_autoencoder_results(
    model_name,
    val_dataset,
    test_dataset,
    output_dir,
    anomaly_labels,
    batch_size=2048,
):
    param_model = torch.load(f"{output_dir}/best_model_{model_name}.pth", weights_only=True)
    model = models.AutoencoderModel.get_model(val_dataset.num_features, param_model)
    print(model)

    val_scores, val_labels = _reconstruction_errors(model, val_dataset, batch_size)
    test_scores, test_labels = _reconstruction_errors(model, test_dataset, batch_size)

    val_binary = _binary_labels(val_labels, anomaly_labels)
    test_binary = _binary_labels(test_labels, anomaly_labels)

    _plot_reconstruction_hist(val_scores, val_binary, output_dir, model_name, "val")
    _plot_reconstruction_hist(test_scores, test_binary, output_dir, model_name, "test")

    threshold = _best_f1_threshold(val_scores, val_binary)
    _plot_reconstruction_events(val_scores, val_binary, output_dir, model_name, "val", threshold=threshold)
    _plot_reconstruction_events(test_scores, test_binary, output_dir, model_name, "test", threshold=threshold)

    roc_auc = _plot_binary_roc(test_scores, test_binary, output_dir, model_name)
    pr_auc = _plot_binary_pr(test_scores, test_binary, output_dir, model_name)
    confusion_summary = _plot_binary_confusion(test_scores, test_binary, threshold, output_dir, model_name)

    summary = {
        "threshold": threshold,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        **confusion_summary,
    }

    with open(f"{output_dir}/autoencoder_metrics_{model_name}.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    val_dataset.close()
    test_dataset.close()
    return 0
