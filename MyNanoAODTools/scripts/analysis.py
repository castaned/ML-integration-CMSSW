#!/usr/bin/env python3

import os
import sys
import ROOT
import math
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object

class LeptonAnalysis(Module):
    def __init__(self, outputFile):
        self.minLeptons = 2
        self.outputFile = outputFile
        self.histograms = {}
        self.out_branches = ["invariant_mass"]

    def beginJob(self):
        self.outputFile = ROOT.TFile(self.outputFile, "RECREATE")
        self.histograms["electron_pt"] = ROOT.TH1F("electron_pt", "Electron pT; pT (GeV); Events", 50, 0, 200)
        self.histograms["muon_pt"] = ROOT.TH1F("muon_pt", "Muon pT; pT (GeV); Events", 50, 0, 200)
        self.histograms["invariant_mass"] = ROOT.TH1F("invariant_mass", "Invariant Mass of Leading Electrons; Mass (GeV); Events", 50, 0, 200)

    def analyze(self, event):
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        
        good_electrons = sorted([ele for ele in electrons if ele.pt > 20 and abs(ele.eta) < 2.4], key=lambda x: x.pt, reverse=True)
        good_muons = [mu for mu in muons if mu.pt > 20 and abs(mu.eta) < 2.4]
        
        for ele in good_electrons:
            self.histograms["electron_pt"].Fill(ele.pt)
        for mu in good_muons:
            self.histograms["muon_pt"].Fill(mu.pt)
        
        # Compute invariant mass if at least two good electrons are found
        invariant_mass = 0
        if len(good_electrons) >= 2:
            e1, e2 = good_electrons[:2]
            invariant_mass = self.computeInvariantMass(e1, e2)
            self.histograms["invariant_mass"].Fill(invariant_mass)
        
        self.out.fillBranch("invariant_mass", invariant_mass)
        return len(good_electrons) + len(good_muons) >= self.minLeptons
    
    def computeInvariantMass(self, lepton1, lepton2):
        e1, px1, py1, pz1 = self.getLorentzVector(lepton1)
        e2, px2, py2, pz2 = self.getLorentzVector(lepton2)
        mass2 = (e1 + e2) ** 2 - (px1 + px2) ** 2 - (py1 + py2) ** 2 - (pz1 + pz2) ** 2
        return math.sqrt(mass2) if mass2 > 0 else 0
    
    def getLorentzVector(self, lepton):
        e = math.sqrt(lepton.pt**2 * math.cosh(lepton.eta)**2 + 0.000511**2)  # Electron mass ~0.511 MeV
        px = lepton.pt * math.cos(lepton.phi)
        py = lepton.pt * math.sin(lepton.phi)
        pz = lepton.pt * math.sinh(lepton.eta)
        return e, px, py, pz
    
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
    justcount=False,
    outputbranchsel=None  # Ensures new branches are written
)
p.run()


