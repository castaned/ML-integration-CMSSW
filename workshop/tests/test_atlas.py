import sys
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from train_atlas import ams,select_threshold,prepare


class AtlasTests(unittest.TestCase):
    def test_tied_threshold_matches_selected_yields(self):
        labels=np.array([1,0,1,0]);scores=np.array([.8,.8,.4,.1]);weights=np.array([2.,4.,2.,4.])
        threshold,value=select_threshold(labels,scores,weights,10.)
        selected=scores>=threshold
        self.assertAlmostEqual(value,float(ams(weights[selected & (labels==1)].sum(),
                                                weights[selected & (labels==0)].sum())))
        self.assertEqual(float(ams(0,20)),0)

    def test_private_data_cannot_change_preprocessing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'input.csv'
            frame=pd.DataFrame({'EventId':np.arange(100),'Label':['s','b']*50,
                'KaggleSet':['t']*80+['v']*20,'Weight':np.ones(100),'KaggleWeight':np.ones(100),
                'PRI_x':np.arange(100,dtype=float)})
            config={'data':{'input':str(path),'features':'all_physics','missing_value':-999},
                    'split':{'seed':16,'validation_fraction':.2}}
            frame.to_csv(path,index=False);first=prepare(config)
            frame.loc[frame.KaggleSet=='v','PRI_x']=1e20
            frame.to_csv(path,index=False);second=prepare(config)
            np.testing.assert_array_equal(first[5],second[5])
            np.testing.assert_array_equal(first[6],second[6])
            self.assertEqual(len(first[0]),80)
            self.assertAlmostEqual(first[8].sum(),80.)
            config['data']['features']=['Weight']
            with self.assertRaises(ValueError):prepare(config)
