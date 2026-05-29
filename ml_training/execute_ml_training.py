import argparse
import sys
import utilities.prepare as prepare
import utilities.utils as utils
import models.models as models
import src.optimize_model as opt
import src.test_results as tr
import traceback
import os


def _resolve_input_paths(data_config):
    if data_config.get("input_paths_normal") or data_config.get("input_paths_anomaly"):
        return list(data_config.get("input_paths_normal", [])) + list(data_config.get("input_paths_anomaly", []))
    return utils.require_key(data_config, "input_paths")


def _load_label_mapping(data_config):
    label_mapping_path = data_config.get("label_mapping")
    if not label_mapping_path:
        return None
    label_mapping = utils.read_json(label_mapping_path)
    return utils.int_key_in_dict(label_mapping)


def _build_mlp_datasets(data_config):
    input_paths = _resolve_input_paths(data_config)
    input_paths = [os.path.abspath(data_path) for data_path in input_paths]
    features = utils.require_key(data_config, "features")
    label = utils.require_key(data_config, "label")
    num_classes = utils.require_key(data_config, "num_classes")

    full_dataset = prepare.h5Dataset(input_paths, features, label, num_classes)
    train_idx, test_idx = prepare.split_h5Dataset(full_dataset, 0.2, 16)

    train_dataset = prepare.h5Dataset(
        input_paths,
        features,
        label,
        num_classes,
        transform=models.MLPTransform(),
        indices=[full_dataset.global_ids[i] for i in train_idx],
    )

    test_dataset = prepare.h5Dataset(
        input_paths,
        features,
        label,
        num_classes,
        transform=models.MLPTransform(),
        indices=[full_dataset.global_ids[i] for i in test_idx],
    )

    return full_dataset, train_dataset, None, test_dataset


def _build_autoencoder_datasets(config, data_config):
    input_paths = _resolve_input_paths(data_config)
    input_paths = [os.path.abspath(data_path) for data_path in input_paths]
    features = utils.require_key(data_config, "features")
    label = utils.require_key(data_config, "label")
    num_classes = utils.require_key(data_config, "num_classes")

    anomaly_config = utils.require_key(config, "anomaly_detection")
    normal_labels = utils.require_key(anomaly_config, "normal_labels")
    anomaly_labels = utils.require_key(anomaly_config, "anomaly_labels")
    val_size = anomaly_config.get("val_size", 0.2)
    test_size = anomaly_config.get("test_size", 0.2)
    seed = anomaly_config.get("seed", 16)

    full_dataset = prepare.h5Dataset(input_paths, features, label, num_classes)
    split_ids = prepare.build_autoencoder_splits(
        full_dataset,
        normal_labels=normal_labels,
        anomaly_labels=anomaly_labels,
        val_size=val_size,
        test_size=test_size,
        seed=seed,
    )

    train_dataset = prepare.h5Dataset(
        input_paths,
        features,
        label,
        num_classes,
        transform=models.AutoencoderTransform(),
        indices=split_ids["train_normal"],
    )

    val_dataset = prepare.h5Dataset(
        input_paths,
        features,
        label,
        num_classes,
        transform=models.AutoencoderTransform(),
        indices=split_ids["val_normal"],
    )

    val_mixed_dataset = prepare.h5Dataset(
        input_paths,
        features,
        label,
        num_classes,
        transform=models.AutoencoderTransform(),
        indices=split_ids["val_mixed"],
    )

    test_dataset = prepare.h5Dataset(
        input_paths,
        features,
        label,
        num_classes,
        transform=models.AutoencoderTransform(),
        indices=split_ids["test_mixed"],
    )

    return full_dataset, train_dataset, val_dataset, val_mixed_dataset, test_dataset


def main(config_path):
    config = prepare.load_config(config_path)

    data_config = utils.require_key(config, "data")
    output_dir = utils.require_key(data_config, "output_path")

    if not os.path.isabs(output_dir):
        output_dir = os.path.abspath(output_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    sys.stdout = utils.TimestampedLogger(sys.stdout, f"{output_dir}/stdout.log")
    sys.stderr = utils.TimestampedLogger(sys.stderr, f"{output_dir}/stderr.log")

    full_dataset = None
    train_dataset = None
    val_dataset = None
    val_mixed_dataset = None
    test_dataset = None

    try:
        label_mapping = _load_label_mapping(data_config)
        model_config = utils.require_key(config, "model")
        model_name = utils.require_key(model_config, "name")
        model_type = utils.require_key(model_config, "type")
        num_models = model_config.get("num_models", 1)

        print("Collecting data...")
        if model_type == "mlp":
            full_dataset, train_dataset, val_dataset, test_dataset = _build_mlp_datasets(data_config)
        elif model_type == "autoencoder":
            full_dataset, train_dataset, val_dataset, val_mixed_dataset, test_dataset = _build_autoencoder_datasets(config, data_config)
        else:
            raise ValueError(f"The model type '{model_type}' is not available.")
        print("Data collected.")

        print("Training and optimizing model...")
        if model_type == "mlp":
            ideal_acc = utils.require_key(model_config, "ideal_accuracy")
            opt.tune_mlp(model_name, model_type, train_dataset, ideal_acc, num_models, output_dir)
            print("MLP training and optimization completed.")
        elif model_type == "autoencoder":
            ideal_loss = model_config.get("ideal_loss")
            opt.tune_autoencoder(model_name, model_type, train_dataset, val_dataset, ideal_loss, num_models, output_dir)
            print("Autoencoder training and optimization completed.")

        print("Testing model...")
        if model_type == "mlp":
            tr.test_results(model_name, model_type, test_dataset, output_dir, class_labels=label_mapping)
            print("MLP testing completed.")
        elif model_type == "autoencoder":
            anomaly_labels = utils.require_key(utils.require_key(config, "anomaly_detection"), "anomaly_labels")
            tr.test_autoencoder_results(model_name, val_mixed_dataset, test_dataset, output_dir, anomaly_labels)
            print("Autoencoder testing completed.")

    except Exception:
        error_message = traceback.format_exc()
        sys.stderr.write(f"[ERROR] {error_message}")

    finally:
        if full_dataset is not None:
            full_dataset.close()
        if train_dataset is not None:
            train_dataset.close()
        if val_dataset is not None:
            val_dataset.close()
        if val_mixed_dataset is not None:
            val_mixed_dataset.close()
        if test_dataset is not None:
            test_dataset.close()

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train IA models")
    parser.add_argument("-f", "--file", type=str, help="Path to the configuration file.", required=True)
    args = parser.parse_args()

    main(args.file)
