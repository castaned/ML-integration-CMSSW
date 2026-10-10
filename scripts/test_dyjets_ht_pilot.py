"""Lightweight pilot checks: no PyTorch or cluster required."""
import ast
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import os
import sys
from types import SimpleNamespace

import h5py
import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[1]


class PilotTests(unittest.TestCase):
    def test_empty_arrays_use_uncompressed_storage(self):
        tree = ast.parse((REPO / "data_processing/utilities/root.py").read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "write_carray")
        scope = {}
        exec(compile(ast.Module(body=[node], type_ignores=[]), "writer", "exec"), scope)
        handle = Mock()
        scope["write_carray"](np.empty((0,)), handle, "empty")
        handle.create_array.assert_called_once()
        handle.create_carray.assert_not_called()
        scope["write_carray"](np.ones(2), handle, "filled")
        handle.create_carray.assert_called_once()

    def test_empty_tree_quarantines_stale_h5_before_skip_existing(self):
        tree = ast.parse((REPO / "data_processing/convert_h5/execute_convert_root2h5.py").read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            inputs = base / "DYJets"
            inputs.mkdir()
            (inputs / "empty.root").touch()
            (inputs / "valid.root").touch()
            output = base / "h5/DYJets"
            output.mkdir(parents=True)
            (output / "empty.h5").write_bytes(b"incomplete")
            config = {"scheduler": "slurm", "slurm_params": {}, "convertion": {
                "conda_env": "test", "input_dirs": [str(inputs)], "tree_name": "Events",
                "branches": ["MET_pt"], "eos_output_dir": str(base / "h5"),
                "max_jagged_len": None}}
            utils = Mock()
            utils.load_config.return_value = config
            utils.require_key.side_effect = lambda obj, key: obj[key]
            lxplus = Mock()
            def open_root(path):
                context = Mock()
                context.__enter__ = Mock(return_value={"Events": SimpleNamespace(
                    num_entries=0 if Path(path).stem == "empty" else 2)})
                context.__exit__ = Mock(return_value=False)
                return context
            scope = {"os": os, "utils": utils, "lxplus": lxplus,
                     "__file__": str(REPO / "data_processing/convert_h5/execute_convert_root2h5.py"),
                     "parent_dir": str(REPO / "data_processing")}
            exec(compile(ast.Module(body=[node], type_ignores=[]), "converter", "exec"), scope)
            with patch.dict(sys.modules, {"uproot": SimpleNamespace(open=open_root)}):
                scope["main"]("config", skip_empty_trees=True, skip_existing=True)
            self.assertFalse((output / "empty.h5").exists())
            self.assertEqual((output / "empty.h5.empty-root").read_bytes(), b"incomplete")
            args = utils.write_args_file.call_args.args[1]
            self.assertEqual(len(args), 1)
            self.assertIn("valid.root", args[0])

    def test_transverse_mass_uses_selected_channel_and_wrapped_angle(self):
        tree = ast.parse((REPO / "ml_training/src/autoencoder.py").read_text())
        nodes = [n for n in tree.body if
                 isinstance(n, ast.FunctionDef) and n.name == "_channel_feature" or
                 isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and
                    t.id in ("CHANNEL_FEATURES", "CHANNELS") for t in n.targets)]
        scope = {"np": np}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "features", "exec"), scope)
        with tempfile.TemporaryDirectory() as directory:
            with h5py.File(Path(directory) / "test.h5", "w") as h:
                h["MET_pt"] = [100., 100.]
                h["MET_phi"] = [0., -np.pi]
                for channel in "ABCD":
                    h[f"{channel}_pass"] = [int(channel == "A"), int(channel == "B")]
                    h[f"{channel}_Lep3W_pt"] = [25. if channel == "A" else -999.,
                                               25. if channel == "B" else -999.]
                    h[f"{channel}_Lep3W_phi"] = [np.pi, np.pi]
                result = scope["_channel_feature"](h, "W_mt", 2, "test")
                np.testing.assert_allclose(result, [100., 0.], atol=1e-4)

    def test_configs_replace_inclusive_dy_and_preserve_originals(self):
        spec = importlib.util.spec_from_file_location("pilot", REPO / "scripts/setup_dyjets_ht_pilot.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            processing = {"proxy": {"generate": 0}, "data_processing": {
                "slurm_params": {"account": "test"}}}
            conversion = {"slurm_params": {"account": "test"}, "convertion": {"branches": []}}
            model = {"data": {"anomaly_input_paths": ["signal"], "normal_labels": [4, 5, 6]},
                     "model": {"latent_dim": 2}, "anomaly_detection": {"seed": 16}}
            originals = {}
            for name, config in (("sm_cocktail_processing_config.yaml", processing),
                                 ("sm_cocktail_root2h5_config.yaml", conversion),
                                 ("autoencoder_sm_cocktail_dy102_ptsum_config.yaml", model)):
                originals[name] = yaml.safe_dump(config)
                (base / name).write_text(originals[name])
            for ht in module.BINS:
                folder = base / "Data" / f"DYJets_HT{ht}"
                folder.mkdir(parents=True)
                (folder / f"{ht}.root").touch()
            module.generate(base)
            p = yaml.safe_load((base / "dyjets_ht_processing_config.yaml").read_text())
            self.assertEqual(len(p["data_processing"]["datasets"]), 1)
            self.assertEqual(len(p["data_processing"]["datasets"][0]["files"]), 4)
            configs = [yaml.safe_load((base / f"autoencoder_dyjets_ht_{n}features_config.yaml").read_text()) for n in (5, 10)]
            self.assertEqual(configs[0]["data"]["normal_input_paths"], configs[1]["data"]["normal_input_paths"])
            self.assertEqual(configs[0]["anomaly_detection"], configs[1]["anomaly_detection"])
            self.assertEqual(len(configs[1]["data"]["features"]), 10)
            for name, text in originals.items():
                self.assertEqual((base / name).read_text(), text)
            with self.assertRaises(FileExistsError):
                module.generate(base)

    def test_single_bin_does_not_require_other_downloads(self):
        spec = importlib.util.spec_from_file_location("pilot", REPO / "scripts/setup_dyjets_ht_pilot.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            inputs = {
                "sm_cocktail_processing_config.yaml": {"proxy": {}, "data_processing": {
                    "slurm_params": {"account": "test"}}},
                "sm_cocktail_root2h5_config.yaml": {"slurm_params": {}, "convertion": {"branches": []}},
                "autoencoder_sm_cocktail_dy102_ptsum_config.yaml": {"data": {}, "model": {}},
            }
            for name, config in inputs.items():
                (base / name).write_text(yaml.safe_dump(config))
            folder = base / "Data/DYJets_HT70to100"
            folder.mkdir(parents=True)
            (folder / "sample.root").touch()
            module.generate(base, bins=["70to100"])
            config = yaml.safe_load((base / "dyjets_ht_processing_config.yaml").read_text())
            self.assertEqual(config["data_processing"]["datasets"][0]["files"],
                             [str(folder / "sample.root")])


if __name__ == "__main__":
    unittest.main()
