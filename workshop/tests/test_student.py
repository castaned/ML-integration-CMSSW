import sys
from pathlib import Path
import copy
import unittest
import tempfile
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from student import validate,prepare


class StudentTests(unittest.TestCase):
    def test_personal_setup_resolves_shared_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for sample in ('Higgs125','ZZ4L'):
                folder=root/'shared'/sample;folder.mkdir(parents=True)
                (folder/'test.root').touch()
            sm=root/'sm';signal=root/'signal';sm.mkdir();signal.mkdir()
            ref=root/'ae.yaml'
            ref.write_text(yaml.safe_dump({'data':{'normal_input_paths':[str(sm)],'anomaly_input_paths':[str(signal)],'features':['MET_pt','M3l','Z_pt','W_mt','Z_mass']},'model':{'type':'autoencoder'}}))
            settings=root/'settings.yaml'
            settings.write_text(yaml.safe_dump({'nanoaod_root':str(root/'shared'),'slurm_account':'test_account','autoencoder_reference':str(ref)}))
            state=prepare(settings,2,root/'student')
            self.assertEqual(state['group'],2)
            self.assertEqual(state['account'],'test_account')
            path=state['configs']['higgs']['variation']
            c=yaml.safe_load(Path(path).read_text())
            self.assertEqual(c['data']['input'],str(root/'student/extraction/baseline/events.h5'))
            self.assertTrue((root/'student/course_state.json').exists())
            with self.assertRaises(FileExistsError):prepare(settings,2,root/'student')

    def test_only_assigned_parameter_can_change(self):
        base={'workshop':{'parameter':'learning_rate'},'data':{'input':'shared.csv'},
              'model':{'learning_rate':0.001,'hidden_dims':[32,16]},'split':{'seed':16}}
        modified=copy.deepcopy(base);modified['model']['learning_rate']=0.0003
        validate(modified,base,'variation')
        with self.assertRaises(ValueError):validate(modified,base,'baseline')
        modified['split']['seed']=123
        with self.assertRaises(ValueError):validate(modified,base,'variation')
        modified=copy.deepcopy(base);modified['data']['input']='different.csv'
        with self.assertRaises(ValueError):validate(modified,base,'variation')


if __name__=='__main__':unittest.main()
