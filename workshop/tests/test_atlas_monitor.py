import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitor_atlas import epoch_records, render


class MonitorTests(unittest.TestCase):
    def test_log_headers_partial_rows_and_progress_are_ignored(self):
        row = {'epoch': 1, 'train_loss': .5, 'validation_loss': .4, 'validation_auc': .8}
        log = 'Device: cpu\n' + json.dumps(row) + '\n[##---] Epoca 1/20\n{"epoch":2'
        self.assertEqual(epoch_records(log), [row])
        self.assertEqual(epoch_records('{"epoch":1,"train_loss":NaN}'), [])

    def test_early_stop_does_not_claim_all_epochs_ran(self):
        rows = [{'epoch': 1, 'train_loss': .5, 'validation_loss': .4, 'validation_auc': .8},
                {'epoch': 2, 'train_loss': .3, 'validation_loss': .45, 'validation_auc': .81}]
        metrics = {'best_epoch': 1, 'roc_auc_unweighted': .8, 'ams_validation_tuned': 2.5}
        text = render(rows, 20, metrics)
        self.assertIn('Época 2/20', text)
        self.assertIn('Modelo conservado: época 1', text)
        self.assertIn('Entrenamiento terminado', text)

    def test_empty_log_is_waiting_not_completed(self):
        self.assertIn('Esperando', render([], 20))


if __name__ == '__main__':
    unittest.main()
