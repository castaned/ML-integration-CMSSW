"""Download small original CMS NanoAOD files from a verified portal manifest."""
import argparse
import json
from pathlib import Path
import urllib.request
import zlib


def download(folder, per_sample):
    if per_sample not in (1,2): raise ValueError('Pilot manifest contains two files per sample')
    manifest=json.loads((Path(__file__).parent/'configs/cms_nanoaod_sources.json').read_text())
    folder=Path(folder).expanduser()
    for name, sample in manifest.items():
        for item in sample['files'][:per_sample]:
            target=folder/name/item['filename']
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists(): raise FileExistsError(target)
            url='https://opendata.cern.ch'+item['uri'].split('eospublic.cern.ch/')[1].replace('//','/')
            checksum,size=1,0
            partial=target.with_suffix('.root.part')
            with urllib.request.urlopen(url,timeout=120) as response, partial.open('xb') as stream:
                while block:=response.read(1024*1024):
                    stream.write(block); size+=len(block); checksum=zlib.adler32(block,checksum)
            if size!=item['size'] or f'adler32:{checksum & 0xffffffff:08x}'!=item['checksum']:
                raise ValueError(f'Checksum/size mismatch: {partial}')
            partial.rename(target)
            print(target)
    (folder/'sources.json').write_text(json.dumps(manifest,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True)
    p.add_argument('--files-per-sample',type=int,default=2)
    a=p.parse_args();download(a.output,a.files_per_sample)
