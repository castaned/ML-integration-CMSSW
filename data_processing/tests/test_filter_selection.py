import importlib.util
import math
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class _Output:
    def __init__(self):
        self.declared = set()
        self.values = {}

    def branch(self, name, dtype):
        self.declared.add(name)

    def fillBranch(self, name, value):
        if name not in self.declared:
            raise AssertionError(f"Undeclared output branch: {name}")
        self.values[name] = value


class _InputTree:
    def SetBranchStatus(self, name, status):
        pass


def _load_filter():
    root = Path(__file__).resolve().parents[2]
    path = root / "example_files/main_process/filterNanoAOD.py"
    fake_tools = types.ModuleType("mini_nanotools")
    fake_tools.PostProcessor = object
    fake_tools.Module = object
    fake_tools.Collection = lambda event, name: getattr(event, name)
    with patch.dict(sys.modules, {"ROOT": types.ModuleType("ROOT"),
                                  "mini_nanotools": fake_tools}):
        spec = importlib.util.spec_from_file_location("filter_under_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module.LeptonFilter


class FilterSelectionTests(unittest.TestCase):
    def test_only_three_lepton_z_and_w_events_are_written(self):
        lepton_filter = _load_filter()
        electrons = [types.SimpleNamespace(pt=pt, eta=0.1, phi=0.2,
                                           cutBased=4, pdgId=11, charge=charge)
                     for pt, charge in ((80, -1), (60, 1), (55, -1))]

        def run(leptons, has_z, has_w):
            module = lepton_filter.__new__(lepton_filter)
            module.dataset_id = 2
            module.minLeptons = 3
            output = _Output()
            module.beginFile(None, None, _InputTree(), output)
            module.findBestZCandidate = lambda good: (
                has_z, (good[0], good[1]) if has_z else None, 91.0 if has_z else None)
            module.findBestWCandidate = lambda remaining: (
                has_w, remaining[0] if has_w else None)
            module.dr_l1l2_Z = lambda pair: (0.3, 0.2, 0.1)
            module.WMass = lambda lepton, met_pt, met_phi: 80.0
            module.Total_Mass = lambda l1, l2, l3: 200.0
            event = types.SimpleNamespace(Electron=leptons, Muon=[], MET_pt=50.0,
                                          MET_phi=0.0, HLT_Mu50=0,
                                          HLT_Ele32_WPTight_Gsf=1)
            return module.analyze(event), output.values, module.cutflow

        self.assertFalse(run(electrons[:2], False, False)[0])
        self.assertFalse(run(electrons, False, False)[0])
        self.assertFalse(run(electrons, True, False)[0])
        passed, values, cutflow = run(electrons, True, True)
        self.assertTrue(passed)
        self.assertEqual([values[name] for name in
                          ("3Lep_pass", "Z_pass", "W_pass", "A_pass")], [1, 1, 1, 1])
        self.assertEqual(cutflow["w"], 1)
        self.assertEqual(cutflow["A"], 1)

    def test_channel_c_angles_and_muon_energy(self):
        lepton_filter = _load_filter()
        module = lepton_filter.__new__(lepton_filter)
        module.dataset_id = 2
        module.minLeptons = 3
        output = _Output()
        module.beginFile(None, None, _InputTree(), output)
        electron = types.SimpleNamespace(pt=55, eta=0.1, phi=0.2,
                                         cutBased=4, pdgId=11, charge=-1)
        muons = [types.SimpleNamespace(pt=pt, eta=0.2, phi=0.3, ip3d=0.001,
                                       highPtId=2, pdgId=13, charge=charge)
                 for pt, charge in ((80, -1), (70, 1))]
        module.findBestZCandidate = lambda good: (True, (good[1], good[2]), 91.0)
        module.findBestWCandidate = lambda remaining: (True, remaining[0])
        module.dr_l1l2_Z = lambda pair: (0.3, 0.2, 0.1)
        module.WMass = lambda lepton, met_pt, met_phi: 80.0
        module.Total_Mass = lambda l1, l2, l3: 200.0
        event = types.SimpleNamespace(Electron=[electron], Muon=muons, MET_pt=50.0,
                                      MET_phi=0.0, HLT_Mu50=1,
                                      HLT_Ele32_WPTight_Gsf=0)

        self.assertTrue(module.analyze(event))
        self.assertEqual([output.values[name] for name in
                          ("C_Dr_Z", "C_Dphi_Z", "C_Deta_Z")], [0.3, 0.2, 0.1])
        energy = module.getLorentzVector(muons[0])[0]
        self.assertAlmostEqual(energy, math.sqrt(80**2 * math.cosh(0.2)**2 + 0.105**2))


if __name__ == "__main__":
    unittest.main()
