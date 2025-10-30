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


# --- Configure the certified JSON *here* ---
# If you ship "Cert_Run3_Golden.json" with Condor, it lands in the job's workdir
JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "Cert_314472-325175_13TeV_Legacy2018_Collisions18_JSON.txt"))
# Alternatively, point to an absolute path:
# JSON_PATH = "/eos/user/u/you/certs/Cert_Collisions2023_366403_370790_Golden.json"


# --- helper: DATA if no genWeight branch ---
def is_data_file(path):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie(): raise RuntimeError(f"Cannot open: {path}")
    t = f.Get("Events")
    if not t: raise RuntimeError(f"'Events' tree missing in: {path}")
    has_genw = bool(t.GetBranch("genWeight"))
    f.Close()
    return not has_genw


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

        branches = ["Zmass", "Wmass", "Dr_Z", "Dphi_Z","Deta_Z", "Sum_pt", "Sum_mass", "ptZ","nlep","pass"]
        
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

        self.out.branch(f"B_mu1ip3d", "F")
        self.out.branch(f"C_mu1ip3d", "F")
        self.out.branch(f"C_mu2ip3d", "F")
        self.out.branch(f"D_mu1ip3d", "F")
        self.out.branch(f"D_mu2ip3d", "F")
        self.out.branch(f"D_mu3ip3d", "F")

        self.out.branch("Dataset_ID", "I")  # Store dataset as integer
        self.out.branch("3Lep_pass", "I")
        self.out.branch("Z_pass", "I")
        self.out.branch("W_pass", "I")
        self.out.branch("A_Wpass", "I")
        self.out.branch("B_Wpass", "I")
        self.out.branch("C_Wpass", "I")
        self.out.branch("D_Wpass", "I")
        self.out.branch("nLeptons", "I")
        self.out.branch("HLTMU50", "I")
        self.out.branch("HLTEle32", "I")
 
 
        inputTree.SetBranchStatus("event",1)
        inputTree.SetBranchStatus("luminosityBlock",1)
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
        inputTree.SetBranchStatus("Muon_ip3d",1)
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
        good_electrons = sorted([ele for ele in electrons if ele.pt > 10 and abs(ele.eta) < 2.5 and ele.cutBased >= 2 ], key=lambda x: x.pt, reverse=True) 
                
        #---------------MUONES
        good_muons = sorted([mu for mu in muons if mu.pt > 20 and abs(mu.eta) < 2.4 and mu.ip3d < 0.01 and mu.highPtId >= 1 ], key=lambda x: x.pt, reverse=True)


        self.out.fillBranch("A_pass", 0)
        self.out.fillBranch("B_pass", 0)
        self.out.fillBranch("C_pass", 0)
        self.out.fillBranch("D_pass", 0)

        self.out.fillBranch("3Lep_pass",0)
        self.out.fillBranch("Z_pass",0)
        self.out.fillBranch("W_pass",0)
        self.out.fillBranch("A_Wpass",0)
        self.out.fillBranch("B_Wpass",0)
        self.out.fillBranch("C_Wpass",0)
        self.out.fillBranch("D_Wpass",0)

        self.out.fillBranch("A_nlep",0);
        self.out.fillBranch("A_ptZ",-999);
        self.out.fillBranch("A_Dr_Z",-999);
        self.out.fillBranch("A_Dphi_Z",-999);
        self.out.fillBranch("A_Deta_Z",-999);
        self.out.fillBranch("A_Zmass",-999);
        self.out.fillBranch("A_Lep1Z_pt",-999);
        self.out.fillBranch("A_Lep2Z_pt",-999);
        self.out.fillBranch("A_Lep1Z_eta",-999);
        self.out.fillBranch("A_Lep2Z_eta",-999);
        self.out.fillBranch("A_Lep1Z_phi",-999);
        self.out.fillBranch("A_Lep2Z_phi",-999);        
        self.out.fillBranch("A_Wmass",-999);        
        self.out.fillBranch("A_Sum_mass",-999);        
        self.out.fillBranch("A_Lep3W_pt",-999);        
        self.out.fillBranch("A_Lep3W_eta",-999);        
        self.out.fillBranch("A_Lep3W_phi",-999);

        self.out.fillBranch("B_nlep",0);
        self.out.fillBranch("B_ptZ",-999);
        self.out.fillBranch("B_Dr_Z",-999);
        self.out.fillBranch("B_Dphi_Z",-999);
        self.out.fillBranch("B_Deta_Z",-999);
        self.out.fillBranch("B_Zmass",-999);
        self.out.fillBranch("B_Lep1Z_pt",-999);
        self.out.fillBranch("B_Lep2Z_pt",-999);
        self.out.fillBranch("B_Lep1Z_eta",-999);
        self.out.fillBranch("B_Lep2Z_eta",-999);
        self.out.fillBranch("B_Lep1Z_phi",-999);
        self.out.fillBranch("B_Lep2Z_phi",-999);        
        self.out.fillBranch("B_Wmass",-999);        
        self.out.fillBranch("B_Sum_mass",-999);        
        self.out.fillBranch("B_Lep3W_pt",-999);        
        self.out.fillBranch("B_Lep3W_eta",-999);        
        self.out.fillBranch("B_Lep3W_phi",-999);

        self.out.fillBranch("C_nlep",0);
        self.out.fillBranch("C_ptZ",-999);
        self.out.fillBranch("C_Dr_Z",-999);
        self.out.fillBranch("C_Dphi_Z",-999);
        self.out.fillBranch("C_Deta_Z",-999);
        self.out.fillBranch("C_Zmass",-999);
        self.out.fillBranch("C_Lep1Z_pt",-999);
        self.out.fillBranch("C_Lep2Z_pt",-999);
        self.out.fillBranch("C_Lep1Z_eta",-999);
        self.out.fillBranch("C_Lep2Z_eta",-999);
        self.out.fillBranch("C_Lep1Z_phi",-999);
        self.out.fillBranch("C_Lep2Z_phi",-999);        
        self.out.fillBranch("C_Wmass",-999);        
        self.out.fillBranch("C_Sum_mass",-999);        
        self.out.fillBranch("C_Lep3W_pt",-999);        
        self.out.fillBranch("C_Lep3W_eta",-999);        
        self.out.fillBranch("C_Lep3W_phi",-999);

        self.out.fillBranch("D_nlep",0);
        self.out.fillBranch("D_ptZ",-999);
        self.out.fillBranch("D_Dr_Z",-999);
        self.out.fillBranch("D_Dphi_Z",-999);
        self.out.fillBranch("D_Deta_Z",-999);
        self.out.fillBranch("D_Zmass",-999);
        self.out.fillBranch("D_Lep1Z_pt",-999);
        self.out.fillBranch("D_Lep2Z_pt",-999);
        self.out.fillBranch("D_Lep1Z_eta",-999);
        self.out.fillBranch("D_Lep2Z_eta",-999);
        self.out.fillBranch("D_Lep1Z_phi",-999);
        self.out.fillBranch("D_Lep2Z_phi",-999);        
        self.out.fillBranch("D_Wmass",-999);        
        self.out.fillBranch("D_Sum_mass",-999);        
        self.out.fillBranch("D_Lep3W_pt",-999);        
        self.out.fillBranch("D_Lep3W_eta",-999);        
        self.out.fillBranch("D_Lep3W_phi",-999);        
        
        good_leptons = good_electrons + good_muons
        
        self.out.fillBranch("nLeptons", len(good_leptons)) #numero de leptones por evento

        
        if len(good_leptons) >= self.minLeptons:

            self.out.fillBranch("3Lep_pass",1);

            foundZ, pair, best_Zmass = self.findBestZCandidate(good_leptons)
            
            if foundZ:
                self.out.fillBranch("Z_pass",1);

                l1,l2 = pair

                leptons = [lepton for lepton in good_leptons if lepton not in (l1, l2)]
                                
                foundW, lepW = self.findBestWCandidate(leptons)

                if foundW:

                     self.out.fillBranch("W_pass",1);
                     
                     ####### A channel (eeenu) ############
                     if abs(l1.pdgId) == 11 and abs(l2.pdgId) == 11 and abs(lepW.pdgId) == 11:  
                
                         self.out.fillBranch("A_pass", 1)
                         self.out.fillBranch("A_nlep", len(good_leptons))
                        
                         lepton1_pt = l1.pt
                         lepton2_pt = l2.pt
                         lepton1_eta = l1.eta
                         lepton2_eta = l2.eta
                         lepton1_phi = l1.phi
                         lepton2_phi = l2.phi
                         ptZ = math.sqrt(l1.pt**2 + l2.pt**2)
                       
                         dr,dphi,deta = self.dr_l1l2_Z(pair)
                         self.out.fillBranch("A_ptZ", ptZ)
                         self.out.fillBranch("A_Dr_Z", dr)
                         self.out.fillBranch("A_Dphi_Z", dphi)
                         self.out.fillBranch("A_Deta_Z", deta)
                         self.out.fillBranch("A_Zmass", best_Zmass)
                         self.out.fillBranch("A_Lep1Z_pt", lepton1_pt)
                         self.out.fillBranch("A_Lep2Z_pt", lepton2_pt)
                         self.out.fillBranch("A_Lep1Z_eta", lepton1_eta)
                         self.out.fillBranch("A_Lep2Z_eta", lepton2_eta)
                         self.out.fillBranch("A_Lep1Z_phi", lepton1_phi)
                         self.out.fillBranch("A_Lep2Z_phi", lepton2_phi)
                        
                         lepton3_pt = lepW.pt
                         lepton3_eta = lepW.eta
                         lepton3_phi = lepW.phi
                        
                         W_mass = self.WMass(lepW, met_pt, met_phi)
                         self.out.fillBranch("A_Wmass", W_mass)
                
                         total_mass = self.Total_Mass(l1,l2, lepW)
                         self.out.fillBranch("A_Sum_mass", total_mass)
                         self.out.fillBranch("A_Lep3W_pt", lepton3_pt)
                         self.out.fillBranch("A_Lep3W_eta", lepton3_eta)
                         self.out.fillBranch("A_Lep3W_phi", lepton3_phi)
                           
                         total_pt = lepton1_pt + lepton2_pt + lepton3_pt
                         self.out.fillBranch("A_Sum_pt", total_pt)


                         ####### B channel (eemunu) ############
                     if abs(l1.pdgId) == 11 and abs(l2.pdgId) == 11 and abs(lepW.pdgId) == 13:  
                
                         self.out.fillBranch("B_pass", 1)
                         self.out.fillBranch("B_nlep", len(good_leptons))
                        
                         lepton1_pt = l1.pt
                         lepton2_pt = l2.pt
                         lepton1_eta = l1.eta
                         lepton2_eta = l2.eta
                         lepton1_phi = l1.phi
                         lepton2_phi = l2.phi
                         ptZ = math.sqrt(l1.pt**2 + l2.pt**2)
                       
                         dr,dphi,deta = self.dr_l1l2_Z(pair)
                         self.out.fillBranch("B_ptZ", ptZ)
                         self.out.fillBranch("B_Dr_Z", dr)
                         self.out.fillBranch("B_Dphi_Z", dphi)
                         self.out.fillBranch("B_Deta_Z", deta)
                         self.out.fillBranch("B_Zmass", best_Zmass)
                         self.out.fillBranch("B_Lep1Z_pt", lepton1_pt)
                         self.out.fillBranch("B_Lep2Z_pt", lepton2_pt)
                         self.out.fillBranch("B_Lep1Z_eta", lepton1_eta)
                         self.out.fillBranch("B_Lep2Z_eta", lepton2_eta)
                         self.out.fillBranch("B_Lep1Z_phi", lepton1_phi)
                         self.out.fillBranch("B_Lep2Z_phi", lepton2_phi)
                        
                         lepton3_pt = lepW.pt
                         lepton3_eta = lepW.eta
                         lepton3_phi = lepW.phi
                        
                         W_mass = self.WMass(lepW, met_pt, met_phi)
                         self.out.fillBranch("B_Wmass", W_mass)
                
                         total_mass = self.Total_Mass(l1,l2, lepW)
                         self.out.fillBranch("B_Sum_mass", total_mass)
                         self.out.fillBranch("B_Lep3W_pt", lepton3_pt)
                         self.out.fillBranch("B_Lep3W_eta", lepton3_eta)
                         self.out.fillBranch("B_Lep3W_phi", lepton3_phi)
                           
                         total_pt = lepton1_pt + lepton2_pt + lepton3_pt
                         self.out.fillBranch("B_Sum_pt", total_pt)

                         ####### C channel (mumue) ############
                     if abs(l1.pdgId) == 13 and abs(l2.pdgId) == 13 and abs(lepW.pdgId) == 11 and ( (l1.highPtId == 2 and (l2.highPtId == 1 or l2.highPtId == 2)) or (l2.highPtId == 2 and (l1.highPtId == 1 or l1.highPtId == 2)) ):
                         
                         self.out.fillBranch("C_pass", 1)
                         self.out.fillBranch("C_nlep", len(good_leptons))
                        
                         lepton1_pt = l1.pt
                         lepton2_pt = l2.pt
                         lepton1_eta = l1.eta
                         lepton2_eta = l2.eta
                         lepton1_phi = l1.phi
                         lepton2_phi = l2.phi
                         ptZ = math.sqrt(l1.pt**2 + l2.pt**2)
                       
                         dr,dphi,deta = self.dr_l1l2_Z(pair)
                         self.out.fillBranch("C_ptZ", ptZ)
                         self.out.fillBranch("C_Dr_Z", dr)
                         self.out.fillBranch("C_Dr_Z", dphi)
                         self.out.fillBranch("C_Zmass", best_Zmass)
                         self.out.fillBranch("C_Lep1Z_pt", lepton1_pt)
                         self.out.fillBranch("C_Lep2Z_pt", lepton2_pt)
                         self.out.fillBranch("C_Lep1Z_eta", lepton1_eta)
                         self.out.fillBranch("C_Lep2Z_eta", lepton2_eta)
                         self.out.fillBranch("C_Lep1Z_phi", lepton1_phi)
                         self.out.fillBranch("C_Lep2Z_phi", lepton2_phi)
                        
                         lepton3_pt = lepW.pt
                         lepton3_eta = lepW.eta
                         lepton3_phi = lepW.phi
                        
                         W_mass = self.WMass(lepW, met_pt, met_phi)
                         self.out.fillBranch("C_Wmass", W_mass)
                
                         total_mass = self.Total_Mass(l1,l2, lepW)
                         self.out.fillBranch("C_Sum_mass", total_mass)
                         self.out.fillBranch("C_Lep3W_pt", lepton3_pt)
                         self.out.fillBranch("C_Lep3W_eta", lepton3_eta)
                         self.out.fillBranch("C_Lep3W_phi", lepton3_phi)
                           
                         total_pt = lepton1_pt + lepton2_pt + lepton3_pt
                         self.out.fillBranch("C_Sum_pt", total_pt)

                         ####### D channel (mumumum) ############
                     if abs(l1.pdgId) == 13 and abs(l2.pdgId) == 13 and abs(lepW.pdgId) == 13 and( (l1.highPtId == 2 and (l2.highPtId == 1 or l2.highPtId == 2)) or (l2.highPtId == 2 and (l1.highPtId == 1 or l1.highPtId == 2)) ):

                
                         self.out.fillBranch("D_pass", 1)
                         self.out.fillBranch("D_nlep", len(good_leptons))
                        
                         lepton1_pt = l1.pt
                         lepton2_pt = l2.pt
                         lepton1_eta = l1.eta
                         lepton2_eta = l2.eta
                         lepton1_phi = l1.phi
                         lepton2_phi = l2.phi
                         ptZ = math.sqrt(l1.pt**2 + l2.pt**2)
                       
                         dr,dphi,deta = self.dr_l1l2_Z(pair)
                         self.out.fillBranch("D_ptZ", ptZ)
                         self.out.fillBranch("D_Dr_Z", dr)
                         self.out.fillBranch("D_Dphi_Z", dphi)
                         self.out.fillBranch("D_Deta_Z", deta)
                         self.out.fillBranch("D_Zmass", best_Zmass)
                         self.out.fillBranch("D_Lep1Z_pt", lepton1_pt)
                         self.out.fillBranch("D_Lep2Z_pt", lepton2_pt)
                         self.out.fillBranch("D_Lep1Z_eta", lepton1_eta)
                         self.out.fillBranch("D_Lep2Z_eta", lepton2_eta)
                         self.out.fillBranch("D_Lep1Z_phi", lepton1_phi)
                         self.out.fillBranch("D_Lep2Z_phi", lepton2_phi)
                        
                         lepton3_pt = lepW.pt
                         lepton3_eta = lepW.eta
                         lepton3_phi = lepW.phi
                        
                         W_mass = self.WMass(lepW, met_pt, met_phi)
                         self.out.fillBranch("D_Wmass", W_mass)
                
                         total_mass = self.Total_Mass(l1,l2, lepW)
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
        
    def findBestZCandidate(self, leptons, z_mass: float = 91.1876):
        import itertools
        best_pair = None
        best_mass = None
        min_diff = float("inf")
        
        for l1, l2 in itertools.combinations(leptons, 2):
          # SFOS requirement
           if (l1.charge + l2.charge) != 0:
              continue
           if abs(l1.pdgId) != abs(l2.pdgId):
              continue

           mass = self.computeInvariantMass(l1, l2)
           diff = abs(mass - z_mass)

           if diff < min_diff:
              min_diff = diff
              best_pair = (l1, l2)
              best_mass = mass

        return (best_pair is not None), best_pair, best_mass


    def findBestWCandidate(self, leptons):
        best_lep = None
        max_pt = -1.0
        
        for lepton in leptons:
            if abs(lepton.pdgId) == 11:
                if lepton.cutBased == 4 and lepton.pt >= 50 and lepton.pt > max_pt:
                    best_lep = lepton
                    max_pt = lepton.pt
            elif abs(lepton.pdgId) == 13:
                if lepton.highPtId == 2 and lepton.pt >= 70 and lepton.pt > max_pt:
                    best_lep = lepton
                    max_pt = lepton.pt
                    
        return (best_lep is not None), best_lep    
    
    
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
        if best_pair:           # 
           lepton1, lepton2 = best_pair
           dphi = (lepton1.phi - lepton2.phi + math.pi) % (2 * math.pi) - math.pi
           deta = lepton1.eta - lepton2.eta # 
           dr = math.sqrt(dphi**2 + deta**2) 
           return dr,dphi,deta
        else:
           return 0
               

# Main execution
inputFile = sys.argv[1]
dataset_folder = sys.argv[2]
outputDir = sys.argv[3]

mods = [LeptonFilter(dataset_folder)]

# 1) Build kwargs FIRST
pp_kwargs = dict(
    outputDir=outputDir,
    inputFiles=[inputFile],
    cut=None,
    branchsel="src/DeepNTuples/new_dataproc/example/branchsel.txt",
    outputbranchsel=None,
    modules=mods,
    noOut=False,
    justcount=False,
)

# 2) Add JSON only for DATA
if is_data_file(inputFile):
    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError(f"Detected DATA but JSON not found: {JSON_PATH}")
    pp_kwargs["jsonInput"] = JSON_PATH  # filter bad lumis BEFORE modules

# 3) Run
p = PostProcessor(**pp_kwargs)
p.run()



