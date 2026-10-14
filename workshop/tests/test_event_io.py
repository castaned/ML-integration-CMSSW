import sys
from pathlib import Path
import tempfile
import unittest
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from event_io import write_events_h5,read_events_h5
from train_higgs import run


class EventIOTests(unittest.TestCase):
    def test_roundtrip_and_training(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            frame=pd.DataFrame({'EventId':[f'file:événement:{i}' for i in range(200)],
                'Label':['b','s']*100,'PRI_met':[float(i%7) for i in range(200)]})
            target=folder/'events.h5'
            write_events_h5(frame,target)
            pd.testing.assert_frame_equal(frame,read_events_h5(target))
            with self.assertRaises(FileExistsError):write_events_h5(frame,target)
            config={'data':{'input':str(target),'features':['PRI_met'],'max_events':0},
                    'split':{'seed':16},'model':{'type':'logistic','max_iter':100},
                    'evaluation':{'background_acceptance':0.1}}
            metrics=run(config,folder/'results')
            self.assertEqual(metrics['counts'],{'train':120,'validation':40,'test':40})


if __name__=='__main__':unittest.main()
