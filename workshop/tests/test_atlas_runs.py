import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from atlas_runs import reserve_run, run_from_log


class RunFoldersTests(unittest.TestCase):
    def test_existing_results_preserved_and_numbers_not_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            (base/'metrics.json').write_text('old results')
            (base/'run_0007').mkdir()
            self.assertEqual(reserve_run(base).name, 'run_0008')
            self.assertEqual((base/'metrics.json').read_text(), 'old results')

    def test_simultaneous_reservations_are_unique(self):
        with tempfile.TemporaryDirectory() as temp:
            with ThreadPoolExecutor(max_workers=8) as pool:
                paths = list(pool.map(lambda _: reserve_run(temp), range(16)))
            self.assertEqual(len(set(paths)), 16)
            self.assertTrue(all(p.is_dir() for p in paths))

    def test_monitor_uses_folder_recorded_by_this_job(self):
        self.assertIsNone(run_from_log('waiting\nTraceback\n'))
        self.assertEqual(run_from_log(json.dumps({'run_directory': '/results/run_0012'})),
                         Path('/results/run_0012'))
