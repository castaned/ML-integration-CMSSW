"""Verify figure generation with synthetic scores, never presented as results."""
import csv
import ast
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
import numpy as np
import yaml


class PosterTests(unittest.TestCase):
    def test_variable_histograms_share_full_range_and_normalization(self):
        tree = ast.parse(Path(__file__).with_name("plot_poster_variables.py").read_text())
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "draw"
                 or isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in
                    ("LABELS", "COLORS") for t in n.targets)]
        scope = {"np": np}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "variables", "exec"), scope)
        groups = {"DYJets": np.array([[1.], [2.]]), "Wprime": np.array([[10.], [20.]])}
        ax = Mock()
        scope["draw"](ax, "MET_pt", 0, groups)
        calls = ax.hist.call_args_list
        self.assertEqual(len(calls), 2)
        np.testing.assert_array_equal(calls[0].kwargs["bins"], calls[1].kwargs["bins"])
        self.assertEqual(calls[0].kwargs["bins"][0], 1.)
        self.assertEqual(calls[0].kwargs["bins"][-1], 20.)
        self.assertTrue(all(call.kwargs["density"] for call in calls))

    def test_figures_and_auc_consistency(self):
        spec = importlib.util.spec_from_file_location("poster", Path(__file__).with_name("make_poster_plots.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            config = {"data": {"output_path": str(folder), "features": list(range(10))},
                      "model": {"name": "test", "hidden_dims": [16, 8], "latent_dim": 2}}
            path = folder / "config.yaml"
            path.write_text(yaml.safe_dump(config))
            metrics = {"threshold": 2.5, "roc_auc": 1.0, "signal_test": 2,
                       "normal_test_by_id": {"4": 2, "5": 2, "6": 2},
                       "normal_process_names": {"4": "DYJets", "5": "WZ", "6": "ZZ"}}
            metric_path = folder / "metrics_test.json"
            metric_path.write_text(json.dumps(metrics))
            with (folder / "scores_test.csv").open("w", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["sample", "anomaly_score", "above_threshold"])
                for name in ("DYJets_test", "WZ_test", "ZZ_test", "signal_example"):
                    for score in ([3, 4] if name == "signal_example" else [1, 2]):
                        writer.writerow([name, score, int(score >= 2.5)])
            with patch.object(sys, "argv", ["poster", "-f", str(path)]):
                module.main()
            for stem in ("ROC", "PR", "scores", "scores_by_process", "architecture"):
                for extension in ("pdf", "png"):
                    self.assertGreater((folder / "poster_figures_10variables" / f"{stem}.{extension}").stat().st_size, 100)
            metrics["roc_auc"] = 0.5
            metric_path.write_text(json.dumps(metrics))
            with self.assertRaisesRegex(ValueError, "AUC"):
                module.load_scores(config)


if __name__ == "__main__":
    unittest.main()
