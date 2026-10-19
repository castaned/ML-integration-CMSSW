import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import yaml

from workshop.setup_cms import generate, PROCESSES


class SetupCMSTest(unittest.TestCase):
    def test_connected_configs_and_preservation(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            for name, (directory, _) in PROCESSES.items():
                path = base / 'inputs' / directory / 'nested'
                path.mkdir(parents=True)
                (path / f'{name}.root').touch()
            with contextlib.redirect_stdout(io.StringIO()):
                paths = generate(base / 'inputs', base / 'personal')
            configs = {key: yaml.safe_load(path.read_text()) for key, path in paths.items()}
            p = configs['processing']['data_processing']
            c = configs['root2h5']['convertion']
            a = configs['autoencoder']['data']
            self.assertEqual(c['input_dirs'], [str(Path(p['eos_output_dir']) / n) for n in PROCESSES])
            self.assertEqual(a['normal_input_paths'], [str(Path(c['eos_output_dir']) / n) for n in ('DYJets', 'WZ', 'ZZ')])
            self.assertEqual(a['anomaly_input_paths'], [str(Path(c['eos_output_dir']) / 'Wprime')])
            self.assertEqual(a['normal_labels'], [4, 5, 6])
            self.assertEqual(a['anomaly_labels'], [1])
            self.assertEqual(len(a['features']), 10)
            for channel in 'ABCD':
                for suffix in ('pass', 'Lep3W_pt', 'Lep3W_phi', 'Sum_mass', 'ptZ'):
                    self.assertIn(f'{channel}_{suffix}', c['branches'])
            manifest = json.loads((base / 'personal/configs/cms_inputs_baseline01.json').read_text())
            self.assertTrue(all(Path(files[0]).is_file() for files in manifest.values()))
            original = paths['autoencoder'].read_bytes()
            with self.assertRaises(FileExistsError):
                generate(base / 'inputs', base / 'personal')
            self.assertEqual(original, paths['autoencoder'].read_bytes())

    def test_missing_inputs_write_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            with self.assertRaises(FileNotFoundError):
                generate(base / 'missing', base / 'personal')
            self.assertFalse((base / 'personal').exists())

    def test_duplicate_basenames_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            for sub in ('one', 'two'):
                path = base / 'inputs/DYjets' / sub
                path.mkdir(parents=True)
                (path / 'same.root').touch()
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                generate(base / 'inputs', base / 'personal')


if __name__ == '__main__':
    unittest.main()
