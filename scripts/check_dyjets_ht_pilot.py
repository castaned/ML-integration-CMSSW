"""Validate all pilot features and process counts before training."""
import argparse
from pathlib import Path
import sys

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ml_training"))
from src.autoencoder import _load_events, _split_by_process


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-f", "--file", type=Path, required=True)
    args = parser.parse_args()
    config = yaml.safe_load(args.file.read_text())
    data = config["data"]
    values, ids = _load_events(data["normal_input_paths"], data["features"],
                               data["label"], data["normal_labels"], return_labels=True)
    if set(np.unique(ids)) != set(data["normal_labels"]):
        raise ValueError("Missing SM process")
    detection = config["anomaly_detection"]
    _, labels = _split_by_process(values, ids, detection["validation_fraction"],
                                  detection["test_fraction"], detection["seed"])
    for process_id in sorted(np.unique(ids)):
        counts = [int(np.count_nonzero(part == process_id)) for part in labels]
        print(data["normal_process_names"][int(process_id)],
              "train/validation/test:", counts)
    signal = _load_events(data["anomaly_input_paths"], data["features"],
                          data["label"], data["anomaly_labels"])
    if not len(signal):
        raise ValueError("No signal events")
    if np.any(values < 0) or np.any(signal < 0):
        raise ValueError("Unexpected negative value in nonnegative pilot features")
    print("Wprime evaluation:", len(signal), "events; all features validated")
