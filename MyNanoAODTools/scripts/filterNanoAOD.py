import os
import json
import sys
import ROOT
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
import math
import itertools

MAPPING_FILE = "dataset_mapping.json"  # JSON file to store dataset mappings

def get_dataset_id(dataset_folder):
    """
    Get or generate a unique integer ID for the dataset.
    Updates dataset_mapping.json to store the mapping.
    """
    # Load existing dataset mapping or create a new one
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, "r") as f:
            try:
                dataset_mapping = json.load(f)
            except json.JSONDecodeError:
                dataset_mapping = {}  # Reset mapping if corrupted
    else:
        dataset_mapping = {}

    # Assign a new ID if dataset is not in mapping
    if dataset_folder not in dataset_mapping:
        dataset_id = len(dataset_mapping) + 1  # Incremental unique ID
        dataset_mapping[dataset_folder] = dataset_id

        # Save updated mapping
        with open(MAPPING_FILE, "w") as f:
            json.dump(dataset_mapping, f, indent=4)
    else:
        dataset_id = dataset_mapping[dataset_folder]

    return dataset_id

class LeptonFilter(Module):
    def __init__(self, dataset_folder):
        self.minLeptons = 3
        self.dataset_id = get_dataset_id(dataset_folder)  # Get dataset ID from JSON

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch("A_Zmass", "F")
        self.out.branch("B_Zmass", "F")
        self.out.branch("C_Zmass", "F")
        self.out.branch("D_Zmass", "F")
        self.out.branch("A_Dr_Z", "F")
        self.out.branch("B_Dr_Z", "F")
        self.out.branch("C_Dr_Z", "F")
        self.out.branch("D_Dr_Z", "F")
        self.out.branch("Dataset_ID", "I")  # Store dataset as integer

        inputTree.SetBranchStatus("Electron_pdgId", 1)
        inputTree.SetBranchStatus("Muon_pdgId", 1)

    def analyze(self, event):
        self.out.fillBranch("Dataset_ID", self.dataset_id)  # Store dataset as integer
        return True  # Continue processing

# Main execution
inputFile = sys.argv[1]
dataset_folder = sys.argv[2]
process = sys.argv[3]
outputDir = f"filteredNanoAOD/{dataset_folder}/{process}"

p = PostProcessor(
    outputDir, [inputFile],
    cut=None,
    branchsel="branchsel.txt",
    outputbranchsel=None,
    modules=[LeptonFilter(dataset_folder)],
    noOut=False,
    justcount=False
)
p.run()

