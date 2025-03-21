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


    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch("A_Zmass", "F") # Invariant mass channel A=eeen
        self.out.branch("B_Zmass", "F") # Invariant mass channel B=eemn
        self.out.branch("C_Zmass", "F") # Invariant mass channel C=mmen
        self.out.branch("D_Zmass", "F") # Invariant mass channel D=mmmn
        self.out.branch("A_Dr_Z", "F")  # dR between leptons channel A
        self.out.branch("B_Dr_Z", "F")  # dR between leptons channel B
        self.out.branch("C_Dr_Z", "F")  # dR between leptons channel C
        self.out.branch("D_Dr_Z", "F")  # dR between leptons channel D
        self.out.branch("MET","F") # MET in the event
        
        inputTree.SetBranchStatus("Electron_pdgId",1)
        inputTree.SetBranchStatus("Muon_pdgId",1)
        
    def analyze(self, event):
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        good_electrons = [ele for ele in electrons if ele.pt > 20 and abs(ele.eta) < 2.4]
        good_muons = [mu for mu in muons if mu.pt > 20 and abs(mu.eta) < 2.4]
        return len(good_electrons) + len(good_muons) >= self.minLeptons

        met_pt = event.MET_pt #este tipo de variables no es un vector y no puede manejarse

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

    

# Read input file from Condor arguments

#if len(sys.argv) < 3:
#    print("Usage: filterNanoAOD.py <input.root> <local folder> <process>")
#    sys.exit(1)


inputFile  = sys.argv[1]
outfolder  = sys.argv[2]
process    = sys.argv[3]
outputDir  = f"filteredNanoAOD/{outfolder}/{process}"  # Corrected
#outputDir = "filteredNanoAOD"

print("++++++++++++++\n")
print("++++++++++++++\n")
print(" input file : ",inputFile)
print(" output folder : ",outfolder)
print(" process       : ",process)
print(" output directory  : ",outputDir)

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
