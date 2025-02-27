#!/usr/bin/env python3

import os
import sys
import ROOT
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection

class LeptonFilter(Module):
    def __init__(self):
        self.minLeptons = 2

    def analyze(self, event):
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        good_electrons = [ele for ele in electrons if ele.pt > 20 and abs(ele.eta) < 2.4]
        good_muons = [mu for mu in muons if mu.pt > 20 and abs(mu.eta) < 2.4]
        return len(good_electrons) + len(good_muons) >= self.minLeptons

# Read input file from Condor arguments
if len(sys.argv) < 2:
    print("Usage: filterNanoAOD.py <input.root>")
    sys.exit(1)

inputFile = sys.argv[1]
outputDir = "filteredNanoAOD"


#branchSelFile = "keepBranches.json"  # Specify the JSON file for branch selection
branchSelFile = "branchsel.txt"

p = PostProcessor(
    outputDir, [inputFile],
    cut=None,
    branchsel=branchSelFile,  # Use branch selection file
    modules=[LeptonFilter()],
    noOut=False,
    justcount=False
)
p.run()


