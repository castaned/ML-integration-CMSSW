import math
import sys
from pathlib import Path
import unittest
import yaml
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from extract_fourleptons import candidate,vector


class SelectionTests(unittest.TestCase):
    def test_pairing_and_rejections(self):
        cuts=yaml.safe_load((Path(__file__).resolve().parents[1]/'configs/cms_fourleptons.yaml').read_text())['selection']
        leptons=[{'pt':pt,'charge':charge,'flavor':13,'v':vector(pt,0,phi,0)}
                 for pt,phi,charge in [(45,0,1),(45,math.pi,-1),(15,math.pi/2,1),(15,3*math.pi/2,-1)]]
        row,stage=candidate(leptons,cuts)
        self.assertEqual(stage,'selected')
        self.assertAlmostEqual(row['DER_mZ1'],90)
        self.assertAlmostEqual(row['DER_mZ2'],30)
        self.assertAlmostEqual(row['DER_m4l'],120)
        self.assertIsNone(candidate(leptons[:3],cuts)[0])
        for lepton in leptons: lepton['charge']=1
        self.assertEqual(candidate(leptons,cuts)[1],'sfos_pairs')


if __name__=='__main__':unittest.main()
