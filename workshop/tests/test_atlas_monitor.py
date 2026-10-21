import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitor_atlas import epoch_records, render, job_status
from unittest.mock import patch
from subprocess import CompletedProcess


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
        self.assertNotIn('AMS', text)

    def test_empty_log_is_waiting_not_completed(self):
        self.assertIn('Esperando', render([], 20))

    def test_pending_and_failed_jobs_are_distinguished(self):
        self.assertIn('EN COLA', render([], 20, state='PENDING', detail='Resources'))
        failed = render([], 20, state='FAILED', log_text='RuntimeError: invalid input')
        self.assertIn('FALLÓ', failed)
        self.assertIn('RuntimeError: invalid input', failed)

    def test_completed_metrics_without_epoch_log_are_shown(self):
        metrics = {'best_epoch': 3, 'roc_auc_unweighted': .9, 'ams_validation_tuned': 2.5}
        self.assertIn('Resultados disponibles', render([], 20, metrics))

    def test_real_losses_appear_on_shared_chart(self):
        row = {'epoch': 1, 'train_loss': .5, 'validation_loss': .4, 'validation_auc': .8}
        text = render([row], 20)
        self.assertIn('0.5000', text)
        self.assertIn('0.4000', text)
        self.assertIn('T: entrenamiento', text)

    @patch('monitor_atlas.subprocess.run')
    def test_accounting_used_after_job_leaves_queue(self, run):
        run.side_effect = [CompletedProcess([], 0, '', ''),
                           CompletedProcess([], 0, 'FAILED|1:0|\n', '')]
        self.assertEqual(job_status('123'), ('FAILED', '1:0'))


if __name__ == '__main__':
    unittest.main()
