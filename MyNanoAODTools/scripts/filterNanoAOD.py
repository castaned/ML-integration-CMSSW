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

        branches = ["Zmass", "Wmass", "Dr_Z", "Sum_pt", "Sum_mass", "nlep"]
        
        for channel in ['A', 'B', 'C', 'D']:
             self.out.branch(f"{channel}_Lep3W_pt", "F")
             self.out.branch(f"{channel}_Lep3W_eta", "F")
             self.out.branch(f"{channel}_Lep3W_phi", "F")
             for branch in branches:
                 self.out.branch(f"{channel}_{branch}", "F")
             for i in range(1, 3):
                 self.out.branch(f"{channel}_Lep{i}Z_pt", "F")
                 self.out.branch(f"{channel}_Lep{i}Z_eta", "F")
                 self.out.branch(f"{channel}_Lep{i}Z_phi", "F")
 
        self.out.branch("Dataset_ID", "I")  # Store dataset as integer
        self.out.branch("nLeptons", "I")
        self.out.branch("HLTMU50", "I")
        self.out.branch("HLTEle32", "I")
 
 
        inputTree.SetBranchStatus("event",1)
        inputTree.SetBranchStatus("Electron_pdgId",1)
        inputTree.SetBranchStatus("Electron_charge",1)
        inputTree.SetBranchStatus("Electron_pt",1)
        inputTree.SetBranchStatus("Electron_eta",1)
        inputTree.SetBranchStatus("Electron_phi",1)
        inputTree.SetBranchStatus("Electron_cutBased",1)      
        inputTree.SetBranchStatus("Muon_highPtId", 1)  
        inputTree.SetBranchStatus("Muon_pt",1)
        inputTree.SetBranchStatus("Muon_eta",1)
        inputTree.SetBranchStatus("Muon_phi",1)
        inputTree.SetBranchStatus("Muon_charge",1)
        inputTree.SetBranchStatus("Muon_pdgId",1)
        inputTree.SetBranchStatus("Muon_mass",1)
        inputTree.SetBranchStatus("MET_phi",1)
        inputTree.SetBranchStatus("HLT_Mu50",1)
        inputTree.SetBranchStatus("HLT_Mu50",1)
        inputTree.SetBranchStatus("HLT_Mu50",1)
        inputTree.SetBranchStatus("HLT_Ele32_WPTight_Gsf",1)

        
    def analyze(self, event):

        self.out.fillBranch("Dataset_ID", self.dataset_id)  # Store dataset as integer

        hltmu50 = event.HLT_Mu50
        hltele32 = event.HLT_Ele32_WPTight_Gsf

        self.out.fillBranch("HLTMU50",hltmu50)
        self.out.fillBranch("HLTEle32",hltele32)
        
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        leptons = list(muons) + list(electrons)
        
        met_pt = event.MET_pt 
        met_phi = event.MET_phi
        
        #---------------ELECTRONES
        good_electrons = sorted([ele for ele in electrons if ele.pt > 10 and abs(ele.eta) < 2.5], key=lambda x: x.pt, reverse=True) 
                
        #---------------MUONES
        good_muons = sorted([mu for mu in muons if mu.pt > 20 and abs(mu.eta) < 2.4], key=lambda x: x.pt, reverse=True)
        
        
        good_leptons = good_electrons + good_muons
        
        self.out.fillBranch("nLeptons", len(good_leptons)) #numero de leptones por evento

        
        if len(good_leptons) >= self.minLeptons and (hltmu50 or hltele32):
        
            ####### A channel ############
            if len(good_electrons) >= 3:  # make sure there are at least 3 electrons per event 
                
                self.out.fillBranch("A_nlep", len(good_electrons))
                
                passed_in_channel = True
                
                best_pair, best_mass_Z = self.findBestZCandidate(good_electrons)
                #if not best_pair:
                #    return False  # No se encontro un par Z

                if best_pair:
                    lepton1, lepton2 = best_pair
                    lepton1_pt = lepton1.pt
                    lepton2_pt = lepton2.pt
                    lepton1_eta = lepton1.eta
                    lepton2_eta = lepton2.eta
                    lepton1_phi = lepton1.phi
                    lepton2_phi = lepton2.phi
                
                    dr = self.dr_l1l2_Z(best_pair)
                    self.out.fillBranch("A_Dr_Z", dr)
                    self.out.fillBranch("A_Zmass", best_mass_Z)
                    self.out.fillBranch("A_Lep1Z_pt", lepton1_pt)
                    self.out.fillBranch("A_Lep2Z_pt", lepton2_pt)
                    self.out.fillBranch("A_Lep1Z_eta", lepton1_eta)
                    self.out.fillBranch("A_Lep2Z_eta", lepton2_eta)
                    self.out.fillBranch("A_Lep1Z_phi", lepton1_phi)
                    self.out.fillBranch("A_Lep2Z_phi", lepton2_phi)

                    leptons = [lepton for lepton in good_electrons if lepton != lepton1 and lepton != lepton2]

                    if len(leptons) >= 1:
                        best_lep = self.findBestWCandidate(leptons, met_pt, met_phi)
                
                        if best_lep:
                            lepton3 = best_lep
                            lepton3_pt = lepton3.pt
                            lepton3_eta = lepton3.eta
                            lepton3_phi = lepton3.phi
                            
                            W_mass = self.WMass(lepton3, met_pt, met_phi)
                            self.out.fillBranch("A_Wmass", W_mass)
                
                            total_mass = self.Total_Mass(lepton1, lepton2, lepton3)
                            self.out.fillBranch("A_Sum_mass", total_mass)
                            self.out.fillBranch("A_Lep3W_pt", lepton3_pt)
                            self.out.fillBranch("A_Lep3W_eta", lepton3_eta)
                            self.out.fillBranch("A_Lep3W_phi", lepton3_phi)
                            
                            total_pt = lepton1_pt + lepton2_pt + lepton3_pt
                            self.out.fillBranch("A_Sum_pt", total_pt)
                
                
    
              # **Canal B**
            if len(good_electrons) >= 2 and len(good_muons) >= 1:  # Make sure there are at least 2 electrons and at least 1 muon
            
                self.out.fillBranch("B_nlep", len(good_electrons) + len(good_muons))
                
                passed_in_channel = True
                
                best_pair, best_mass_Z = self.findBestZCandidate(good_electrons)
                #if not best_pair:
                #    return False  # No se encontro un par Z

                if best_pair:
                    lepton1, lepton2 = best_pair
                    lepton1_pt = lepton1.pt
                    lepton2_pt = lepton2.pt
                    lepton1_eta = lepton1.eta
                    lepton2_eta = lepton2.eta
                    lepton1_phi = lepton1.phi
                    lepton2_phi = lepton2.phi
                    
                    dr = self.dr_l1l2_Z(best_pair)
                    self.out.fillBranch("B_Dr_Z", dr)
                    self.out.fillBranch("B_Zmass", best_mass_Z)
                    self.out.fillBranch("B_Lep1Z_pt", lepton1_pt)
                    self.out.fillBranch("B_Lep2Z_pt", lepton2_pt)
                    self.out.fillBranch("B_Lep1Z_eta", lepton1_eta)
                    self.out.fillBranch("B_Lep2Z_eta", lepton2_eta)
                    self.out.fillBranch("B_Lep1Z_phi", lepton1_phi)
                    self.out.fillBranch("B_Lep2Z_phi", lepton2_phi)

                    leptons = [lepton for lepton in good_muons if lepton != lepton1 and lepton != lepton2]

                    if len(leptons) >= 1:
                        best_lep = self.findBestWCandidate(leptons, met_pt, met_phi)
                
                        if best_lep:
                            lepton3 = best_lep
                            lepton3_pt = lepton3.pt
                            lepton3_eta = lepton3.eta
                            lepton3_phi = lepton3.phi
                            
                            W_mass = self.WMass(lepton3, met_pt, met_phi)
                            self.out.fillBranch("B_Wmass", W_mass)
                            
                            total_mass = self.Total_Mass(lepton1, lepton2, lepton3)
                            self.out.fillBranch("B_Sum_mass", total_mass)
                            self.out.fillBranch("B_Lep3W_pt", lepton3_pt)
                            self.out.fillBranch("B_Lep3W_eta", lepton3_eta)
                            self.out.fillBranch("B_Lep3W_phi", lepton3_phi)
                            
                            total_pt = lepton1_pt + lepton2_pt + lepton3_pt
                            self.out.fillBranch("B_Sum_pt", total_pt)
                
            #  C channel
            if len(good_muons) >= 2 and len(good_electrons) >= 1:
                
                self.out.fillBranch("C_nlep", len(good_electrons) + len(good_muons))
                
                passed_in_channel = True
                
                
                best_pair, best_mass_Z = self.findBestZCandidate(good_muons)
                
                #if not best_pair:
                #    return False  # No se encontro un par Z

                if best_pair:
                    lepton1, lepton2 = best_pair
                    lepton1_pt = lepton1.pt
                    lepton2_pt = lepton2.pt
                    lepton1_eta = lepton1.eta
                    lepton2_eta = lepton2.eta
                    lepton1_phi = lepton1.phi
                    lepton2_phi = lepton2.phi

                    
                    dr = self.dr_l1l2_Z(best_pair)
                    self.out.fillBranch("C_Dr_Z", dr)
                    self.out.fillBranch("C_Zmass", best_mass_Z)
                    self.out.fillBranch("C_Lep1Z_pt", lepton1_pt)
                    self.out.fillBranch("C_Lep2Z_pt", lepton2_pt)
                    self.out.fillBranch("C_Lep1Z_eta", lepton1_eta)
                    self.out.fillBranch("C_Lep2Z_eta", lepton2_eta)
                    self.out.fillBranch("C_Lep1Z_phi", lepton1_phi)
                    self.out.fillBranch("C_Lep2Z_phi", lepton2_phi)
                

                    leptons = [lepton for lepton in good_electrons if lepton != lepton1 and lepton != lepton2]

                    if len(leptons) >= 1:
                        best_lep = self.findBestWCandidate(leptons, met_pt, met_phi)
                
                        if best_lep:
                            lepton3 = best_lep
                            lepton3_pt = lepton3.pt
                            lepton3_eta = lepton3.eta
                            lepton3_phi = lepton3.phi
                            
                            
                            W_mass = self.WMass(lepton3, met_pt, met_phi)
                            self.out.fillBranch("C_Wmass", W_mass)
                            
                            total_mass = self.Total_Mass(lepton1, lepton2, lepton3)
                            self.out.fillBranch("C_Sum_mass", total_mass)
                            self.out.fillBranch("C_Lep3W_pt", lepton3_pt)
                            self.out.fillBranch("C_Lep3W_eta", lepton3_eta)
                            self.out.fillBranch("C_Lep3W_phi", lepton3_phi)
                            
                            total_pt = lepton1_pt + lepton2_pt + lepton3_pt
                            self.out.fillBranch("C_Sum_pt", total_pt)
                
            #### D channel ######
            if len(good_muons) >= 3:
            
                self.out.fillBranch("D_nlep", len(good_muons))
                
                passed_in_channel = True
                

                best_pair, best_mass_Z = self.findBestZCandidate(good_muons)
                #if not best_pair:
                #    return False  # No se encontro un par Z

                if best_pair:
                    lepton1, lepton2 = best_pair
                    lepton1_pt = lepton1.pt
                    lepton2_pt = lepton2.pt
                    lepton1_eta = lepton1.eta
                    lepton2_eta = lepton2.eta
                    lepton1_phi = lepton1.phi
                    lepton2_phi = lepton2.phi

                    
                    dr = self.dr_l1l2_Z(best_pair)
                    self.out.fillBranch("D_Dr_Z", dr)
                    self.out.fillBranch("D_Zmass", best_mass_Z)
                    self.out.fillBranch("D_Lep1Z_pt", lepton1_pt)
                    self.out.fillBranch("D_Lep2Z_pt", lepton2_pt)
                    self.out.fillBranch("D_Lep1Z_eta", lepton1_eta)
                    self.out.fillBranch("D_Lep2Z_eta", lepton2_eta)
                    self.out.fillBranch("D_Lep1Z_phi", lepton1_phi)
                    self.out.fillBranch("D_Lep2Z_phi", lepton2_phi)

                    
                    leptons = [lepton for lepton in good_muons if lepton != lepton1 and lepton != lepton2]

                    if len(leptons) >= 1:
                        best_lep = self.findBestWCandidate(leptons, met_pt, met_phi)
                
                        if best_lep:
                            lepton3 = best_lep
                            lepton3_pt = lepton3.pt
                            lepton3_eta = lepton3.eta
                            lepton3_phi = lepton3.phi
                            
                            
                            W_mass = self.WMass(lepton3, met_pt, met_phi)
                            self.out.fillBranch("D_Wmass", W_mass)
                            
                            total_mass = self.Total_Mass(lepton1, lepton2, lepton3)
                            self.out.fillBranch("D_Sum_mass", total_mass)
                            self.out.fillBranch("D_Lep3W_pt", lepton3_pt)
                            self.out.fillBranch("D_Lep3W_eta", lepton3_eta)
                            self.out.fillBranch("D_Lep3W_phi", lepton3_phi)
                            
                            total_pt = lepton1_pt + lepton2_pt + lepton3_pt
                            self.out.fillBranch("D_Sum_pt", total_pt)
        
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

    def findBestWCandidate(self, leptons, met_pt, met_phi):
        best_lep = None
        found_count = 0  # Contador de candidatos W encontrados
    
        for lepton in leptons:
            if abs(lepton.pdgId) == 11:  # Filtrar por electrones
                if lepton.cutBased == 4 and lepton.pt >= 50 and met_pt > 40:
                    best_lep = lepton
                    found_count += 1  # Incrementar el contador si se encuentra un candidato
    
            if abs(lepton.pdgId) == 13:
                if lepton.highPtId == 2 and lepton.pt >= 70 and met_pt > 40:
                    best_lep = lepton
                    
        if best_lep:
            return best_lep

    def WMass(self, lepton, met_pt, met_phi):
        e, px, py, pz = self.getLorentzVector(lepton)
        
        #El MET puede tratarse como un neutrino con energia igual a MET_pt
        # y phi igual a MET_phi
        met_px = met_pt * math.cos(met_phi)
        met_py = met_pt * math.sin(met_phi)
        
        met_e = met_pt
        
        mass2 = (e + met_e) ** 2 - (px + met_px) ** 2 - (py + met_py) ** 2 - (pz) ** 2
        return math.sqrt(mass2) if mass2 > 0 else 0
        
    def Total_Mass(self, lepton1, lepton2, lepton3):
        
        #Obtener los 4-vectores de los dos leptones
        e1, px1, py1, pz1 = self.getLorentzVector(lepton1)
        e2, px2, py2, pz2 = self.getLorentzVector(lepton2)
        e3, px3, py3, pz3 = self.getLorentzVector(lepton3)

        
        #Calcular la masa invariante (M^2 = E^2 - p^2)
        mass2 = (e1 + e2 + e3) ** 2 - (px1 + px2 + px3) ** 2 - (py1 + py2 + py3) ** 2 - (pz1 + pz2 + pz3) ** 2
        return math.sqrt(mass2) if mass2 > 0 else 0
        
       
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

