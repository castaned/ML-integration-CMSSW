import unittest
from collect_github_traffic import merge_daily


def snapshot(stamp, day, count):
    item = {'timestamp': day + 'T00:00:00Z', 'count': count, 'uniques': 2}
    return {'collected_at_utc': stamp,
            'clones': {'clones': [item]}, 'views': {'views': []}}


class TrafficTests(unittest.TestCase):
    def test_overlapping_windows_replace_instead_of_adding(self):
        first = snapshot('2026-10-17T10:00:00Z', '2026-10-16', 10)
        rows = merge_daily([], first)
        second = snapshot('2026-10-18T10:00:00Z', '2026-10-16', 12)
        rows = merge_daily(rows, second)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['clones'], '12')
        self.assertEqual(rows[0]['views'], '')

    def test_old_capture_cannot_replace_newer_observation(self):
        latest = snapshot('2026-10-18T10:00:00Z', '2026-10-16', 12)
        earlier = snapshot('2026-10-17T10:00:00Z', '2026-10-16', 10)
        self.assertEqual(merge_daily(merge_daily([], latest), earlier)[0]['clones'], '12')

    def test_history_outside_current_window_is_preserved(self):
        rows = merge_daily([], snapshot('2026-10-17T10:00:00Z', '2026-10-16', 10))
        rows = merge_daily(rows, snapshot('2026-11-17T10:00:00Z', '2026-11-16', 20))
        self.assertEqual([row['clones'] for row in rows], ['10', '20'])


if __name__ == '__main__':
    unittest.main()
