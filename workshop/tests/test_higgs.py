"""Synthetic fixtures verify contracts only; they are not HEP performance results."""
import sys
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from train_higgs import prepare, run


class HiggsTests(unittest.TestCase):
    def frame(self):
        rng = np.random.default_rng(42)
        labels = np.tile(['b', 's'], 100)
        x = rng.normal(size=200) + (labels == 's')
        x[::17] = -999
        return pd.DataFrame({'EventId': np.arange(200), 'Label': labels,
                             'PRI_met': x, 'Weight': np.ones(200)})

    def test_splits_and_missingness(self):
        f, x, y, parts = prepare(self.frame(), ['PRI_met'], 16, 100)
        self.assertEqual([len(p) for p in parts], [60, 20, 20])
        self.assertEqual(len(set(np.concatenate(parts))), 100)
        self.assertTrue(np.isnan(x).any())
        for part in parts:
            self.assertEqual(set(y[part]), {0, 1})
        f2, _, _, parts2 = prepare(self.frame(), ['PRI_met'], 16, 100)
        self.assertTrue(f.EventId.equals(f2.EventId))
        for a, b in zip(parts, parts2): np.testing.assert_array_equal(a, b)

    def test_leakage_rejected(self):
        for feature in ('EventId', 'Weight', 'Label', 'KaggleWeight'):
            with self.assertRaises(ValueError): prepare(self.frame(), [feature], 16, 0)

    def test_validation_run_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            self.frame().to_csv(temp / 'input.csv', index=False)
            config = {'data': {'input': str(temp / 'input.csv'), 'features': ['PRI_met'], 'max_events': 0},
                      'split': {'seed': 16}, 'model': {'type': 'logistic', 'max_iter': 100},
                      'evaluation': {'background_acceptance': 0.1}}
            m = run(config, temp / 'run')
            self.assertEqual(m['evaluation_set'], 'validation')
            self.assertEqual(len(pd.read_csv(temp / 'run/scores.csv')), 40)
            self.assertTrue((temp / 'run/classification.pdf').exists())
            with self.assertRaises(FileExistsError): run(config, temp / 'run')


if __name__ == '__main__': unittest.main()
