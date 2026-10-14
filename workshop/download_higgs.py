"""Instructor downloads once; students read a shared, verified CERN dataset."""
import argparse
import json
from pathlib import Path
import urllib.request
import zlib

URL = 'https://opendata.cern.ch/record/328/files/atlas-higgs-challenge-2014-v2.csv.gz'
CHECKSUM = 'e4717bbe'
SIZE = 65630848


def download(target):
    target = Path(target).expanduser()
    if target.exists():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + '.part')
    checksum, size = 1, 0
    try:
        with urllib.request.urlopen(URL, timeout=120) as response, partial.open('xb') as out:
            while block := response.read(1024 * 1024):
                out.write(block)
                checksum = zlib.adler32(block, checksum)
                size += len(block)
        if size != SIZE or f'{checksum & 0xffffffff:08x}' != CHECKSUM:
            raise ValueError('CERN file size/checksum mismatch; do not use this download')
        partial.rename(target)
    except Exception:
        # Keep partial for diagnosis; never replace a previous dataset.
        raise
    manifest = {'source': URL, 'record': 'https://opendata.cern.ch/record/328',
                'doi': '10.7483/OPENDATA.ATLAS.ZBP2.M5T8',
                'bytes': size, 'adler32': CHECKSUM}
    target.with_suffix(target.suffix + '.source.json').write_text(json.dumps(manifest, indent=2))
    print(target)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True)
    download(p.parse_args().output)
