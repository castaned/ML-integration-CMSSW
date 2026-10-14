import sys
from pathlib import Path
import tempfile
import unittest
import json
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from event_io import write_events_h5,read_events_h5
from train_higgs import run,dataset_labels


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

    def test_original_dataset_mapping_protocol(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            mapping=folder/'dataset_map.json'
            mapping.write_text(json.dumps({'1':'Higgs125','2':'ZZ4L'}))
            frame=pd.DataFrame({'EventId':[f'file:{i}' for i in range(200)],
                'Dataset_ID':[2,1]*100,'PRI_met':[float(i%7) for i in range(200)]})
            target=folder/'events.h5'
            write_events_h5(frame,target,dataset_map={1:'Higgs125',2:'ZZ4L'})
            data={'input':str(target),'features':['PRI_met'],'max_events':0,'label':'Dataset_ID',
                  'num_classes':2,'class_id_map':{1:1,2:0},'label_mapping':str(mapping)}
            encoded,names=dataset_labels(read_events_h5(target),data)
            self.assertEqual(encoded.Label.tolist(),['b','s']*100)
            self.assertEqual(names,{1:'Higgs125',0:'ZZ4L'})
            config={'data':data,'split':{'seed':16},'model':{'type':'mlp','max_iter':20,
                    'hidden_dims':[8,4],'learning_rate':0.001},
                    'evaluation':{'background_acceptance':0.1}}
            result=run(config,folder/'results')
            self.assertEqual(result['class_names'][1],'Higgs125')
            self.assertTrue((folder/'results/dataset_map.json').exists())
            data['class_id_map']={1:1,7:0}
            with self.assertRaises(ValueError):dataset_labels(frame,data)


if __name__=='__main__':unittest.main()
