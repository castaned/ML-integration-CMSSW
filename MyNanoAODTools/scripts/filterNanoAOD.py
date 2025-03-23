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

        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        met_pt = event.MET_pt 
        
        leptons = list(muons) + list(electrons)

        if len(leptons) >= 3:
           #print("Eventos seleccionados")
        
           if len(electrons) >= 3:
              #print("Eventos con 3 electrones")
              best_pair, best_mass = self.findBestZCandidate(leptons)
              dr = self.dr_l1l2_Z(best_pair)
              
              self.out.fillBranch("A_Zmass", best_mass)
              self.out.fillBranch("A_Dr_Z", dr)
              
           if len(electrons) >= 2 and len(muons) >= 1:
              #print("Eventos con 3 electrones")
              best_pair, best_mass = self.findBestZCandidate(leptons)
              dr = self.dr_l1l2_Z(best_pair)
              
              self.out.fillBranch("B_Zmass", best_mass)
              self.out.fillBranch("B_Dr_Z", dr) 
              
        
           if len(muons) >= 2 and len(electrons) >= 1:
              #print("Eventos con 3 electrones")
              best_pair, best_mass = self.findBestZCandidate(leptons)
              dr = self.dr_l1l2_Z(best_pair)
              
              self.out.fillBranch("C_Zmass", best_mass)
              
              self.out.fillBranch("C_Dr_Z", dr)
                    
        
           if len(muons) >= 3:
              #print("Eventos con 3 electrones")
              best_pair, best_mass = self.findBestZCandidate(leptons)
              dr = self.dr_l1l2_Z(best_pair)
              
              self.out.fillBranch("D_Zmass", best_mass)
              
              self.out.fillBranch("D_Dr_Z", dr)
        
        return True
              
        
    def etaphiplane(self, lepton1, lepton2):
        dr_etaphi = ()       
    
    def computeInvariantMass(self, lepton1, lepton2):
        e1, px1, py1, pz1 = self.getLorentzVector(lepton1)
        e2, px2, py2, pz2 = self.getLorentzVector(lepton2)
        mass2 = (e1 + e2) ** 2 - (px1 + px2) ** 2 - (py1 + py2) ** 2 - (pz1 + pz2) ** 2
        return math.sqrt(mass2) if mass2 > 0 else 0
    
    def getLorentzVector(self, lepton):
        
        
        m_lepton = 0.000511 if abs(lepton.pdgId) == 11 else 0.105  # Electron: 0.511 MeV, Muon: 105 MeV
        e = math.sqrt(lepton.pt**2 * math.cosh(lepton.eta)**2 + 0.000511**2)  # Electron mass ~0.511 MeV
        px = lepton.pt * math.cos(lepton.phi)
        py = lepton.pt * math.sin(lepton.phi)
        pz = lepton.pt * math.sinh(lepton.eta)
        return e, px, py, pz
        
    def findBestZCandidate(self, leptons):
        Z_MASS = 91.2  # Z boson mass in GeV
        #Finds the lepton pair with invariant mass closest to the Z boson mass"""
        best_pair = None
        best_mass = float("inf")
        min_diff = float("inf")

        for lepton1, lepton2 in itertools.combinations(leptons, 2):
            if lepton1.charge + lepton2.charge != 0:  # Require opposite charge
                continue
            if abs(lepton1.pdgId) != abs(lepton2.pdgId): 
                continue
            
            mass = self.computeInvariantMass(lepton1, lepton2)
            diff = abs(mass - Z_MASS)

            if diff < min_diff:
                min_diff = diff
                best_mass = mass
                best_pair = (lepton1, lepton2)
                
        if best_pair:        
           return best_pair, best_mass  
        else:
           return None, 0.0
           
    def dr_l1l2_Z(self, best_pair):
        dr_max = 1.5
        if best_pair:
           lepton1, lepton2 = best_pair
           dr = math.sqrt((lepton1.phi - lepton2.phi)**2 + (lepton1.eta - lepton2.eta)**2) 
           return dr
        else:
           return 0
               

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

