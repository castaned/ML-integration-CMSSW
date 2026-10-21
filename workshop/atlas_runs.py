"""Reserve numbered ATLAS run folders without overwriting existing results."""
import json
import re
from pathlib import Path


def reserve_run(base, name="run"):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", name):
        raise ValueError("output.run_name must use letters, digits, underscores or hyphens (max 100 characters)")
    prefix = name + "_"
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    numbers = [int(p.name[len(prefix):]) for p in base.iterdir()
               if p.name.startswith(prefix) and p.name[len(prefix):].isdigit()]
    number = max(numbers, default=0) + 1
    while True:
        directory = base / f'{prefix}{number:04d}'
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
