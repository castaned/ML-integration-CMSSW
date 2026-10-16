import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from processing_jobs import submit, merge, worker
from extract_fourleptons import save_results
from event_io import read_events_h5


class ProcessingJobsTests(unittest.TestCase):
    def test_array_and_afterok(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = [root/'a.root', root/'b.root']
            for path in files: path.touch()
            config = {'dataset_map': {1:'Higgs125'}, 'samples': [
                {'name':'Higgs125','ID':1,'files':list(map(str,files))}]}
            cfg = root/'config.yaml'; cfg.write_text(yaml.safe_dump(config))
            with patch('processing_jobs.subprocess.check_output', side_effect=['123;cluster\n','124\n']) as run:
                self.assertEqual(submit(cfg,root/'result','curso07','qoscurso07'),('123','124'))
                self.assertIn('--array=1-2',run.call_args_list[0].args[0])
                self.assertIn('--dependency=afterok:123',run.call_args_list[1].args[0])
                self.assertIn('--qos=qoscurso07',run.call_args_list[0].args[0])
            manifest=root/'result.parts/manifest.json'
            with patch('extract_fourleptons.extract') as extract:
                worker(manifest,2)
                self.assertEqual(extract.call_args.args[0]['samples'][0]['files'],[str(files[1])])
                self.assertTrue(extract.call_args.kwargs['allow_empty'])
            with self.assertRaises(FileExistsError): submit(cfg,root/'result','curso07')

    def test_merge_empty_shard_and_missing_shard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            config={'dataset_map':{1:'Higgs125'},'samples':[]}
            columns=['EventId','Dataset_ID','DER_m4l','DER_mZ1','DER_mZ2']
            empty=pd.DataFrame(columns=columns)
            full=pd.DataFrame([['a:1',1,125.,91.,25.]],columns=columns)
            for i,frame in enumerate([empty,full],1):
                save_results(config,root/f'file_{i:05d}',frame,
                    {'Higgs125':{'input':10,'selected':len(frame)}},[{'file':str(i)}],plots=False)
            manifest=root/'manifest.json'
            data={'config':config,'tasks':[{},{}],'output':str(root/'combined')}
            manifest.write_text(json.dumps(data))
            merge(manifest)
            self.assertEqual(len(read_events_h5(root/'combined/events.h5')),1)
            counts=json.loads((root/'combined/cutflow.json').read_text())
            self.assertEqual(counts['Higgs125'],{'input':20,'selected':1})
            self.assertTrue((root/'combined/observables.png').exists())
            data['tasks'].append({});data['output']=str(root/'incomplete')
            manifest.write_text(json.dumps(data))
            with self.assertRaises(FileNotFoundError): merge(manifest)
            self.assertFalse((root/'incomplete').exists())
