import importlib.util
import csv
import copy
import json
import tempfile
import unittest
from pathlib import Path


DEPENDENCIES = ("numpy", "torch", "h5py", "sklearn", "matplotlib", "onnx")


@unittest.skipUnless(all(importlib.util.find_spec(name) for name in DEPENDENCIES), "ML dependencies are not installed")
class AutoencoderTests(unittest.TestCase):
    def test_training_uses_only_normal_events(self):
        import h5py
        import numpy as np
        import torch
        from src.autoencoder import _split_normal, run_autoencoder

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rng = np.random.default_rng(7)
            normal = rng.normal(size=(60, 3)).astype("f4")
            anomaly = rng.normal(loc=5, size=(12, 3)).astype("f4")
            qcd = rng.normal(loc=2, size=(15, 3)).astype("f4")
            paths = []
            for name, values, label in (("normal", normal, 2), ("anomaly", anomaly, 1),
                                        ("qcd", qcd, 3)):
                path = root / f"{name}.h5"
                with h5py.File(path, "w") as handle:
                    for index in range(3):
                        handle.create_dataset(f"f{index}", data=values[:, index])
                    handle.create_dataset("Dataset_ID", data=np.full(len(values), label))
                paths.append(str(path))

            config = {
                "data": {"normal_input_paths": [paths[0]], "anomaly_input_paths": [paths[1]],
                         "qcd_input_paths": [paths[2]], "qcd_labels": [3],
                         "features": ["f0", "f1", "f2"], "label": "Dataset_ID",
                         "normal_labels": [2], "anomaly_labels": [1]},
                "model": {"name": "trial", "type": "autoencoder", "hidden_dims": [4],
                          "latent_dim": 2, "epochs": 2, "batch_size": 16,
                          "learning_rate": 0.001, "patience": 2, "export_onnx": False},
                "anomaly_detection": {"validation_fraction": 0.2, "test_fraction": 0.2,
                                      "normal_quantile": 0.9, "seed": 11},
            }
            output = root / "results"
            run_autoencoder(config, str(output))
            metrics = json.loads((output / "metrics_trial.json").read_text())
            checkpoint = torch.load(output / "best_model_trial.pth", map_location="cpu", weights_only=True)
            train, _, _ = _split_normal(normal, 0.2, 0.2, 11)

            self.assertEqual(metrics["normal_train"], len(train))
            self.assertEqual(metrics["signal_test"], len(anomaly))
            self.assertEqual(metrics["qcd_test"], len(qcd))
            self.assertGreaterEqual(metrics["qcd_test_fpr"], 0)
            np.testing.assert_allclose(checkpoint["mean"], train.mean(axis=0), rtol=1e-5)
            self.assertLess(np.max(checkpoint["mean"]), 2)
            self.assertTrue((output / "ROC_trial.pdf").is_file())
            self.assertTrue((output / "scores_trial.pdf").is_file())
            self.assertTrue((output / "validation_events_trial.pdf").is_file())
            self.assertTrue((output / "EWK_QCD_trial.pdf").is_file())
            with (output / "scores_trial.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(sum(row["sample"] == "QCD_test" for row in rows), len(qcd))
            self.assertEqual(sum(row["sample"] == "signal_example" for row in rows), len(anomaly))

            mixture = copy.deepcopy(config)
            mixture["data"]["normal_input_paths"] = [paths[0], paths[2]]
            mixture["data"]["normal_labels"] = [2, 3]
            del mixture["data"]["qcd_input_paths"]
            del mixture["data"]["qcd_labels"]
            mixture["model"]["name"] = "mixture"
            mixture_output = root / "mixture_results"
            run_autoencoder(mixture, str(mixture_output))
            mixture_metrics = json.loads((mixture_output / "metrics_mixture.json").read_text())
            mixture_checkpoint = torch.load(mixture_output / "best_model_mixture.pth",
                                            map_location="cpu", weights_only=True)
            ewk_train, _, _ = _split_normal(normal, 0.2, 0.2, 13)
            qcd_train, _, _ = _split_normal(qcd, 0.2, 0.2, 14)
            expected_mean = (ewk_train.mean(axis=0) + qcd_train.mean(axis=0)) / 2
            np.testing.assert_allclose(mixture_checkpoint["mean"], expected_mean, rtol=1e-5)
            self.assertEqual(mixture_metrics["normal_training_by_id"], {"2": 36, "3": 9})
            self.assertEqual(mixture_metrics["normal_validation_by_id"], {"2": 12, "3": 3})
            self.assertEqual(mixture_metrics["normal_test_by_id"], {"2": 12, "3": 3})
            self.assertEqual(mixture_metrics["qcd_test"], 3)
            self.assertEqual(mixture_metrics["signal_test"], len(anomaly))
            self.assertTrue((mixture_output / "EWK_QCD_mixture.pdf").is_file())
            self.assertTrue((mixture_output / "scores_mixture.pdf").is_file())
            self.assertTrue((mixture_output / "scores_by_process_mixture.pdf").is_file())
            self.assertTrue((mixture_output / "validation_events_mixture.pdf").is_file())


if __name__ == "__main__":
    unittest.main()
