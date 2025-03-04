#!/usr/bin/env python3

import os
import sys
import ROOT
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection

class LeptonAnalysis(Module):
    def __init__(self, outputFile):
        self.minLeptons = 2
        self.outputFile = outputFile
        self.histograms = {}

    def beginJob(self):
        self.outputFile = ROOT.TFile(self.outputFile, "RECREATE")
        self.histograms["electron_pt"] = ROOT.TH1F("electron_pt", "Electron pT; pT (GeV); Events", 50, 0, 200)
        self.histograms["muon_pt"] = ROOT.TH1F("muon_pt", "Muon pT; pT (GeV); Events", 50, 0, 200)

    def analyze(self, event):
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        
        good_electrons = [ele for ele in electrons if ele.pt > 20 and abs(ele.eta) < 2.4]
        good_muons = [mu for mu in muons if mu.pt > 20 and abs(mu.eta) < 2.4]
        
        for ele in good_electrons:
            self.histograms["electron_pt"].Fill(ele.pt)
        for mu in good_muons:
            self.histograms["muon_pt"].Fill(mu.pt)
        
        return len(good_electrons) + len(good_muons) >= self.minLeptons
    
    def endJob(self):
        self.outputFile.cd()
        for hist in self.histograms.values():
            hist.Write()
        self.outputFile.Close()

# Read input file and Condor job ID arguments
if len(sys.argv) < 4:
    print("Usage: filterNanoAOD.py <input.root> <cluster_id> <process_id>")
    sys.exit(1)

inputFile = sys.argv[1]
cluster_id = sys.argv[2]  # Condor Cluster ID
process_id = sys.argv[3]  # Condor Process ID

outputDir = "filteredNanoAOD"
os.makedirs(outputDir, exist_ok=True)

# Use Condor job IDs for unique histogram filenames
histOutputFile = os.path.join(outputDir, f"histograms_{cluster_id}_{process_id}.root")
branchSelFile = "branchsel.txt"

p = PostProcessor(
    outputDir, [inputFile],
    cut=None,
    branchsel=branchSelFile,
    modules=[LeptonAnalysis(histOutputFile)],
    noOut=False,
    justcount=False
)
p.run()

