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
tree = upfile['deepntuplizer/Events']

# Define branch groups
other_branches = ['event',
                  'Dataset_ID',
                  'MET_pt',
                  'nElectron',
                  'nMuon',
                  'A_Zmass',
                  'B_Zmass',
                  'C_Zmass',
                  'D_Zmass',
                  'A_Dr_Z',
                  'B_Dr_Z',
                  'C_Dr_Z',
                  'D_Dr_Z']
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


