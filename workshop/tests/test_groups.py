import sys
import json
from pathlib import Path
import tempfile
import unittest
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from setup_groups import generate
from collect_results import collect


class GroupTests(unittest.TestCase):
    def test_generation_collection_and_fair_comparison(self):
        with tempfile.TemporaryDirectory() as temp:
            temp=Path(temp)
            source=temp/'reference.yaml'
            source.write_text(yaml.safe_dump({'data':{'input':'shared.csv','features':['PRI_met']},
                              'model':{'type':'logistic'},'split':{'seed':16}}))
            generate(source,temp/'team1',temp/'results','higgs')
            paths=list((temp/'team1').glob('*.yaml'))
            self.assertEqual(len(paths),8)
            for path in paths:
                config=yaml.safe_load(path.read_text())
                tag=config['workshop']
                out=Path(tag['results_path']);out.mkdir(parents=True)
                (out/'metrics.json').write_text(json.dumps({'evaluation_set':'validation',
                    'roc_auc_unweighted':0.7 if tag['role']=='baseline' else 0.8}))
            rows=collect([temp/'team1'],temp/'summary.csv')
            variations=[r for r in rows if r['role']=='variation']
            self.assertTrue(all(r['interpretation']=='improved_on_validation' for r in variations))
            path=temp/'team1/higgs_group1_variation.yaml'
            config=yaml.safe_load(path.read_text());config['split']['seed']=99
            path.write_text(yaml.safe_dump(config))
            with self.assertRaises(ValueError):collect([temp/'team1'],temp/'invalid.csv')


if __name__=='__main__':unittest.main()
