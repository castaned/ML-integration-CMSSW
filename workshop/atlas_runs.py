"""Reserve numbered ATLAS run folders without overwriting existing results."""
import json
from pathlib import Path


def reserve_run(base):
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    numbers = [int(p.name[4:]) for p in base.iterdir()
               if p.name.startswith('run_') and p.name[4:].isdigit()]
    number = max(numbers, default=0) + 1
    while True:
        directory = base / f'run_{number:04d}'
        try:
            directory.mkdir()
            return directory
        except FileExistsError:
            number += 1


def run_from_log(text):
    for line in text.splitlines():
        try:
            record = json.loads(line)
            if isinstance(record, dict) and record.get('run_directory'):
                return Path(record['run_directory'])
        except (ValueError, TypeError):
            continue
    return None
