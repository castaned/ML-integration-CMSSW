
#!/usr/bin/env python
import os
import sys
import ROOT
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from importlib import import_module

ROOT.PyConfig.IgnoreCommandLineOptions = True

class ExampleAnalysis(Module):
    def __init__(self):  # Corrected method name
        self.writeHistFile = True

    def beginJob(self, histFile=None, histDirName=None):
        Module.beginJob(self, histFile, histDirName)
        self.h_vpt = ROOT.TH1F('sumpt', 'sumpt', 100, 0, 1000)
        self.addObject(self.h_vpt)

    def analyze(self, event):
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        jets = Collection(event, "Jet")
        eventSum = ROOT.TLorentzVector()

        # Select events with at least 2 muons
        if len(muons) >= 2:
            for lep in muons:
                eventSum += lep.p4()
            for lep in electrons:
                eventSum += lep.p4()
            for j in jets:
                eventSum += j.p4()
            self.h_vpt.Fill(eventSum.Pt())

        return True

if __name__ == "__main__":  # Corrected name check
    if len(sys.argv) < 2:
        print("Usage: python analysis.py <input_root_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = os.getcwd()  # Use current directory for Condor job
    preselection = "Jet_pt[0] > 250"

    p = PostProcessor(output_dir, [input_file], cut=preselection, branchsel=None,
                      modules=[ExampleAnalysis()], noOut=True, histFileName="histOut.root", histDirName="plots")
    p.run()
