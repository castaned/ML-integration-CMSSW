import uproot
import pandas
import numpy as np
import pandas as pd
import h5py
import tables
import sys
filters = tables.Filters(complevel=7, complib='blosc')

infile = sys.argv[1]
outfile = sys.argv[2]
entrystop = None
upfile = uproot.open(infile)

tree = upfile['deepntuplizer/tree']

other_branches = ['event_no',  'npv', 'ntrueInt', 'rho', 'sample_isQCD', 'n_pfcands', 'npfcands', 'n_tracks', 'ntracks', 'n_sv', 'nsv']
fj_branches = []
pfcand_branches = []
track_branches = []
sv_branches = []

for branch_name in tree.iterkeys():
    if 'pfcand_' in branch_name:
        pfcand_branches.append(branch_name)
    elif 'track_' in branch_name or 'trackBTag_' in branch_name:
        track_branches.append(branch_name)
    elif 'sv_' in branch_name:
        sv_branches.append(branch_name)
    elif 'fj_' in branch_name:
        fj_branches.append(branch_name)
        
print(other_branches)
print(fj_branches)
print(pfcand_branches)
print(track_branches)
print(sv_branches)

def _write_carray(a, h5file, name, group_path='/', **kwargs):
    h5file.create_carray(group_path, name, obj=a, filters=filters, createparents=True, **kwargs)
    
def _transform(dataframe, max_particles=100, start=0, stop=-1):    
    return dataframe[dataframe.index.get_level_values(-1)<max_particles].unstack().fillna(0)

df_other = tree.pandas.df(branches=other_branches, entrystart=0, entrystop = entrystop)
df_sv = tree.pandas.df(branches=sv_branches, entrystart=0, entrystop = entrystop)
df_track = tree.pandas.df(branches=track_branches, entrystart=0, entrystop = entrystop)
df_pfcand = tree.pandas.df(branches=pfcand_branches, entrystart=0, entrystop = entrystop)
df_fj = tree.pandas.df(branches=fj_branches, entrystart=0, entrystop = entrystop)

with tables.open_file(outfile, mode='w') as h5file:
    
    max_tracks = len(df_track.index.get_level_values(-1).unique())
    max_sv = len(df_sv.index.get_level_values(-1).unique())
    max_pfcand = len(df_pfcand.index.get_level_values(-1).unique())
    print("max_tracks",max_tracks)
    print("max_sv",max_sv)
    print("max_pfcand",max_pfcand)
    
    v_track = _transform(df_track, max_particles = 60)
    for k in track_branches:
        v = np.stack([v_track[(k, i)].values for i in range(60)], axis=-1)
        _write_carray(v, h5file, name=k)
        
    v_sv = _transform(df_sv, max_particles = 5)
    for k in sv_branches:
        v = np.stack([v_sv[(k, i)].values for i in range(5)], axis=-1)
        _write_carray(v, h5file, name=k)
        
    v_pfcand = _transform(df_pfcand, max_particles = 100)
    for k in pfcand_branches:
        v = np.stack([v_pfcand[(k, i)].values for i in range(100)], axis=-1)
        _write_carray(v, h5file, name=k)
        
    for k in df_fj.columns:
        _write_carray(df_fj[k].values, h5file, name=k)
        
    for k in df_other.columns:
        _write_carray(df_other[k].values, h5file, name=k)

f = tables.open_file(outfile)
print(f)
f.close()
