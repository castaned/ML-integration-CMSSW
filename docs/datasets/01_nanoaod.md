# NanoAOD Format

The **NanoAOD** (Nano Analysis Object Data) format is a lightweight and analysis-friendly data format used in the **CMS Experiment** at CERN.  
It is designed to provide a compact representation of event-level information, keeping only the most essential quantities for physics analyses.

---

## Structure Overview

NanoAOD files are ROOT files containing a single `Events` tree with branches for reconstructed and generator-level objects.  
Each branch stores arrays (or collections) of physics objects per event.

Typical groups of branches include:

- **Event information:** run, luminosity block, event ID, generator weight, etc.  
- **Physics objects:**
  - **Electrons** (`Electron_pt`, `Electron_eta`, `Electron_phi`, …)
  - **Muons** (`Muon_pt`, `Muon_eta`, `Muon_iso`, …)
  - **Jets** (`Jet_pt`, `Jet_btag`, `Jet_mass`, …)
  - **Missing transverse energy (MET)** (`MET_pt`, `MET_phi`)
- **Trigger and filter information:** HLT paths, event flags, etc.


## 📚 Documentation & Versioning

The NanoAOD format evolves with each **CMSSW release**, and the detailed documentation — including branch structure, schema definitions, and version notes — is maintained in the official repositories below.

> ⚠️ **Access Warning**  
> The CERN GitLab wiki requires **CMS credentials** (an active CERN account with CMS project access).  
> If you are not logged in, you may see a 404 or "Access Denied" page.

- **Official NanoAOD Documentation Wiki (CERN GitLab)**  
  Detailed versioning information, variable definitions, and schema updates:  
  🔗 [https://gitlab.cern.ch/cms-nanoAOD/nanoaod-doc/-/wikis/home](https://gitlab.cern.ch/cms-nanoAOD/nanoaod-doc/-/wikis/home)

- **NanoAOD-tools on GitHub**  
  Post-processing utilities, friend tree management, and helper scripts for analysis:  
  🔗 [https://github.com/cms-nanoAOD/nanoAOD-tools](https://github.com/cms-nanoAOD/nanoAOD-tools)

- **NanoAOD definitions in CMSSW**  
  Source code for NanoAOD production within the CMSSW framework:  
  🔗 [https://github.com/cms-sw/cmssw/tree/master/PhysicsTools/NanoAOD](https://github.com/cms-sw/cmssw/tree/master/PhysicsTools/NanoAOD)

---


