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
    def test_score_study_balances_sm_processes(self):
        import numpy as np
        from compare_autoencoder_scores import process_weights

        ids = np.array([4, 4, 5, 5, 5, 6])
        weights = process_weights(ids)
        for process_id in (4, 5, 6):
            self.assertAlmostEqual(weights[ids == process_id].sum(), 1 / 3)

    def test_channel_features_follow_the_passing_channel(self):
        import h5py
        import numpy as np
        from src.autoencoder import _load_events

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "channels.h5"
            with h5py.File(path, "w") as handle:
                handle.create_dataset("Dataset_ID", data=[4, 4, 4, 4])
                for index, channel in enumerate("ABCD"):
                    passed = np.zeros(4, dtype=int)
                    passed[index] = 1
                    handle.create_dataset(f"{channel}_pass", data=passed)
                    for branch, offset in (("Sum_mass", 100), ("Dr_Z", 0.1),
                                           ("Zmass", 90), ("Sum_pt", 200)):
                        values = np.full(4, -999.0)
                        values[index] = offset + index
                        handle.create_dataset(f"{channel}_{branch}", data=values)
            values = _load_events([str(path)],
                                  ["M3l", "Z_deltaR", "Z_mass", "Lep_pt_sum"],
                                  "Dataset_ID", [4])
            np.testing.assert_allclose(values[:, 0], [100, 101, 102, 103])
            np.testing.assert_allclose(values[:, 1], [0.1, 1.1, 2.1, 3.1])
            np.testing.assert_allclose(values[:, 2], [90, 91, 92, 93])
            np.testing.assert_allclose(values[:, 3], [200, 201, 202, 203])

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

            cocktail_paths = []
            for process_id, location in ((4, 0), (5, 1), (6, 2)):
                path = root / f"process_{process_id}.h5"
                values = rng.normal(loc=location, size=(30 + 10 * (process_id - 4), 3)).astype("f4")
                with h5py.File(path, "w") as handle:
                    for index in range(3):
                        handle.create_dataset(f"f{index}", data=values[:, index])
                    handle.create_dataset("Dataset_ID", data=np.full(len(values), process_id))
                cocktail_paths.append(str(path))
            cocktail = copy.deepcopy(config)
            cocktail["data"]["normal_input_paths"] = cocktail_paths
            cocktail["data"]["normal_labels"] = [4, 5, 6]
            cocktail["data"]["normal_process_names"] = {4: "DYJets", 5: "WZ", 6: "ZZ"}
            del cocktail["data"]["qcd_input_paths"]
            del cocktail["data"]["qcd_labels"]
            cocktail["model"]["name"] = "cocktail"
            cocktail_output = root / "cocktail_results"
            run_autoencoder(cocktail, str(cocktail_output))
            cocktail_metrics = json.loads((cocktail_output / "metrics_cocktail.json").read_text())
            self.assertEqual(cocktail_metrics["normal_training_by_id"],
                             {"4": 18, "5": 24, "6": 30})
            self.assertEqual(cocktail_metrics["normal_test_by_id"],
                             {"4": 6, "5": 8, "6": 10})
            self.assertEqual(set(cocktail_metrics["normal_test_fpr_by_id"]), {"4", "5", "6"})
            self.assertTrue((cocktail_output / "scores_by_process_cocktail.pdf").is_file())
            with (cocktail_output / "scores_cocktail.csv").open(newline="", encoding="utf-8") as handle:
                names = {row["sample"] for row in csv.DictReader(handle)}
            self.assertEqual(names, {"DYJets_test", "WZ_test", "ZZ_test", "signal_example"})


if __name__ == "__main__":
    unittest.main()
