"""Flat per-event HDF5 arrays, readable with h5py like the CMS autoencoder inputs."""
import json
import h5py
import numpy as np
import pandas as pd


def write_events_h5(frame,path,dataset_map=None):
    with h5py.File(path,'x') as target:
        target.attrs['schema']='workshop-events-v1'
        target.attrs['columns']=json.dumps(frame.columns.tolist())
        if dataset_map is not None:
            target.attrs['dataset_map']=json.dumps(dataset_map)
        elif 'Label' in frame:
            target.attrs['label_mapping']=json.dumps({'b':0,'s':1})
        for name in frame.columns:
            array=frame[name].to_numpy()
            if array.dtype.kind in 'OUS':
                target.create_dataset(name,data=np.asarray(array,dtype=object),
                                      dtype=h5py.string_dtype('utf-8'),compression='gzip')
            else:
                target.create_dataset(name,data=array,compression='gzip')


def read_events_h5(path):
    with h5py.File(path,'r') as source:
        dataset_map=json.loads(source.attrs['dataset_map']) if 'dataset_map' in source.attrs else None
        names=json.loads(source.attrs['columns']) if 'columns' in source.attrs else list(source.keys())
        values={}
        for name in names:
            dataset=source[name]
            if dataset.ndim!=1:raise ValueError(f'{name}: expected one value per event')
            values[name]=dataset.asstr()[:] if h5py.check_string_dtype(dataset.dtype) else dataset[:]
    frame=pd.DataFrame(values)
    if dataset_map is not None:frame.attrs['dataset_map']=dataset_map
    return frame
