#!/usr/bin/env python3

import uproot
import numpy as np
import tables
import awkward as ak
import sys

# Set HDF5 compression filter
filters = tables.Filters(complevel=7, complib='blosc')

# Input/output files from command-line arguments
infile = sys.argv[1]
outfile = sys.argv[2]
entrystop = None  # Process all entries

# Open ROOT file with Uproot
upfile = uproot.open(infile)
#tree = upfile['deepntuplizer/Events']
tree = upfile['Events']

# Define branch groups
other_branches = ['event',
                  'nElectron',
                  'nMuon',
                  'run',
                  'luminosityBlock',
                  'MET_pt',
                  'MET_phi',
                  'HLT_Ele32_WPTight_Gsf',
                  'HLT_Mu50',
                  'HLT_OldMu100',
                  'HLT_Photon200',
                  'HLT_TkMu100',
                  'A_Lep1Z_pt',  
                  'A_Lep2Z_pt',  
                  'A_Lep1Z_eta',
                  'A_Lep2Z_eta', 
                  'A_Lep1Z_phi', 
                  'A_Lep2Z_phi', 
                  'A_Lep3W_pt',  
                  'A_Lep3W_eta', 
                  'A_Lep3W_phi', 
                  'A_ptZ',
                  'A_Zmass',
                  'A_Dr_Z',
                  'A_Sum_pt',
                  'A_Wmass',
                  'A_Sum_mass',
                  'B_Lep1Z_pt',  
                  'B_Lep2Z_pt',  
                  'B_Lep1Z_eta', 
                  'B_Lep2Z_eta', 
                  'B_Lep1Z_phi', 
                  'B_Lep2Z_phi', 
                  'B_Lep3W_pt',  
                  'B_Lep3W_eta', 
                  'B_Lep3W_phi', 
                  'B_ptZ',
                  'B_Zmass',
                  'B_Dr_Z',
                  'B_Sum_pt',
                  'B_Wmass',
                  'B_Sum_mass',
                  'C_Lep1Z_pt',  
                  'C_Lep2Z_pt',  
                  'C_Lep1Z_eta', 
                  'C_Lep2Z_eta', 
                  'C_Lep1Z_phi', 
                  'C_Lep2Z_phi', 
                  'C_Lep3W_pt',  
                  'C_Lep3W_eta', 
                  'C_Lep3W_phi', 
                  'C_ptZ',
                  'C_Zmass',
                  'C_Dr_Z',
                  'C_Sum_pt',
                  'C_Wmass',
                  'C_Sum_mass',
                  'D_Lep1Z_pt',  
                  'D_Lep2Z_pt',  
                  'D_Lep1Z_eta', 
                  'D_Lep2Z_eta', 
                  'D_Lep1Z_phi', 
                  'D_Lep2Z_phi', 
                  'D_Lep3W_pt', 
                  'D_Lep3W_eta', 
                  'D_Lep3W_phi',
                  'D_ptZ',
                  'D_Zmass',
                  'D_Dr_Z',
                  'D_Sum_pt',
                  'D_Wmass',
                  'D_Sum_mass',
                  'A_nlep',      
                  'B_nlep',      
                  'C_nlep',      
                  'D_nlep',
                  'B_mu1ip3d',
                  'C_mu1ip3d',
                  'C_mu2ip3d',
                  'D_mu1ip3d',
                  'D_mu2ip3d',
                  'D_mu3ip3d',
                  'Dataset_ID']
electron_branches = []
muon_branches = []

# Identify electron and muon branches
for branch_name in tree.keys():
    if branch_name.startswith('Electron_'):
        electron_branches.append(branch_name)
    elif branch_name.startswith('Muon_'):
        muon_branches.append(branch_name)

print("Other branches:", other_branches)
print("Electron branches:", electron_branches)
print("Muon branches:", muon_branches)

# Function to write data to HDF5
def _write_carray(a, h5file, name, group_path='/', **kwargs):
    """Writes NumPy array to HDF5 file."""
    h5file.create_carray(group_path, name, obj=a, filters=filters, createparents=True, **kwargs)

# Function to convert and pad awkward arrays
def convert_and_pad(awk_array, max_particles=10, fill_value=0.0):
    """Converts Awkward array to fixed-size NumPy array for HDF5 storage."""
    # Convert to NumPy, pad/truncate to `max_particles`
    padded_array = ak.to_numpy(ak.pad_none(awk_array, max_particles, clip=True))
    padded_array = np.nan_to_num(padded_array, nan=fill_value)  # Replace NaNs with 0
    return padded_array.astype(np.float32)  # Ensure proper dtype

# Load data from ROOT to Awkward Arrays
df_other = tree.arrays(other_branches, entry_start=0, entry_stop=entrystop, library='pd')
df_electron = tree.arrays(electron_branches, entry_start=0, entry_stop=entrystop, library='ak')
df_muon = tree.arrays(muon_branches, entry_start=0, entry_stop=entrystop, library='ak')

# Write to HDF5
with tables.open_file(outfile, mode='w') as h5file:
    # Write event-level branches
    for k in df_other.columns:
        _write_carray(df_other[k].to_numpy().astype(np.float32), h5file, name=k)

    # Write electron branches (converted and padded)
    for k in df_electron.fields:  # Fixed: Use .fields instead of .keys()
        _write_carray(convert_and_pad(df_electron[k]), h5file, name=k)

    # Write muon branches (converted and padded)
    for k in df_muon.fields:  # Fixed: Use .fields instead of .keys()
        _write_carray(convert_and_pad(df_muon[k]), h5file, name=k)

# Verify output
with tables.open_file(outfile, 'r') as f:
    print(f)


