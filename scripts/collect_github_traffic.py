"""Archive aggregate GitHub traffic without double-counting overlapping windows."""
import argparse
import csv
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request


FIELDS = ['date_utc', 'clones', 'clone_uniques', 'views', 'view_uniques',
          'clones_collected_at_utc', 'views_collected_at_utc']


def merge_daily(previous, snapshot):
    """Replace observations for an existing UTC date; never add rolling totals."""
    records = {row['date_utc']: dict(row) for row in previous}
    captured = snapshot['collected_at_utc']
    for kind, unique_key in [('clones', 'clone_uniques'), ('views', 'view_uniques')]:
        for item in snapshot[kind][kind]:
            day = datetime.strptime(item['timestamp'], '%Y-%m-%dT%H:%M:%SZ').date().isoformat()
            count, unique = item['count'], item['uniques']
            if not isinstance(count, int) or not isinstance(unique, int) or not 0 <= unique <= count:
                raise ValueError('Invalid traffic counts')
            row = records.setdefault(day, dict.fromkeys(FIELDS, ''))
            row['date_utc'] = day
            observed_key = kind + '_collected_at_utc'
            if row.get(observed_key, '') <= captured:
                row[kind], row[unique_key] = str(count), str(unique)
                row[observed_key] = captured
    return [records[key] for key in sorted(records)]


def save_snapshot(output, snapshot):
    output = Path(output)
    history = output / 'daily.csv'
    previous = []
    if history.exists():
        with history.open(encoding='utf-8', newline='') as handle:
            previous = list(csv.DictReader(handle))
    rows = merge_daily(previous, snapshot)
    output.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    archive = output / 'snapshots'
    archive.mkdir(exist_ok=True)
    stamp = snapshot['collected_at_utc'].replace(':', '').replace('-', '')
    raw = archive / (stamp + '.json')
    if raw.exists():
        raise FileExistsError(raw)
    raw.write_text(json.dumps(snapshot, indent=2) + '\n', encoding='utf-8')
    temporary = history.with_suffix('.csv.tmp')
    temporary.write_text(buffer.getvalue(), encoding='utf-8', newline='')
    temporary.replace(history)


def token_from_git():
    process = subprocess.run(['git', 'credential', 'fill'],
        input='protocol=https\nhost=github.com\n\n', text=True,
        capture_output=True, check=True, timeout=30)
    values = dict(line.split('=', 1) for line in process.stdout.splitlines() if '=' in line)
    if not values.get('password'):
        raise RuntimeError('GitHub credential unavailable')
    return values['password']


def collect(repository, token):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Expected owner/repository')
    snapshot = {'repository': repository, 'collected_at_utc': '',
                'source': 'GitHub REST API traffic; rolling 14-day windows',
                'attribution': 'Repository-wide; not a count of course participants'}
    for kind in ('clones', 'views'):
        request = urllib.request.Request(
            f'https://api.github.com/repos/{repository}/traffic/{kind}?per=day',
            headers={'Authorization': 'Bearer ' + token,
                     'Accept': 'application/vnd.github+json',
                     'X-GitHub-Api-Version': '2022-11-28',
                     'User-Agent': 'ML-integration-CMSSW-impact'})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f'GitHub {kind}: HTTP {error.code}; check traffic read permissions') from None
        if not all(key in data for key in ('count', 'uniques', kind)):
            raise ValueError('Unexpected GitHub traffic response')
        snapshot[kind] = data
    snapshot['collected_at_utc'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', default='castaned/ML-integration-CMSSW')
    parser.add_argument('--output', type=Path, default=Path('analytics/traffic'))
    parser.add_argument('--git-credential', action='store_true',
                        help='Use the existing local Git credential without persisting it')
    args = parser.parse_args()
    token = token_from_git() if args.git_credential else os.environ.get('GITHUB_TOKEN')
    if not token:
        raise RuntimeError('Set GITHUB_TOKEN or use --git-credential')
    snapshot = collect(args.repository, token)
    save_snapshot(args.output, snapshot)
    print(json.dumps({'saved_to': str(args.output),
        'collected_at_utc': snapshot['collected_at_utc'],
        'rolling_14_day_clones': snapshot['clones']['count'],
        'rolling_14_day_clone_uniques': snapshot['clones']['uniques'],
        'rolling_14_day_views': snapshot['views']['count'],
        'rolling_14_day_view_uniques': snapshot['views']['uniques']}, indent=2))


if __name__ == '__main__':
    main()
