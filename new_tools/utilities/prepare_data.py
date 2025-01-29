# Script to prepare data to train IA models

import tables
import numpy as np
from utilities.read_config_variables import read_variables

def get_features_labels(file_vars, remove_mass_pt_window=True, test=False):

    # Get variables
    if test:
        file_path = 'test_path'
    else:
        file_path = 'train_path'

    variables = read_variables(file_vars, [file_path, 'features', 'spectators', 'labels'])
    #print(variables)
    file_name = variables[file_path][0] 
    features = variables['features']
    spectators = variables['spectators']
    labels = variables['labels']

    nfeatures = len(features)
    nspectators = len(spectators)
    nlabels = len(labels)

    # load file
    h5file = tables.open_file(file_name, 'r')
    njets = getattr(h5file.root,features[0]).shape[0]

    # allocate arrays
    feature_array = np.zeros((njets,nfeatures))
    spec_array = np.zeros((njets,nspectators))
    label_array = np.zeros((njets,nlabels))

    # load arrays
    for (i, feat) in enumerate(features):
        feature_array[:,i] = getattr(h5file.root,feat)[:]

    for (i, spec) in enumerate(spectators):
        spec_array[:,i] = getattr(h5file.root,spec)[:]

    for (i, label) in enumerate(labels):
        prods = label.split('*')
        prod0 = prods[0]
        prod1 = prods[1]
        fact0 = getattr(h5file.root,prod0)[:]
        fact1 = getattr(h5file.root,prod1)[:]
        label_array[:,i] = np.multiply(fact0,fact1)

    # remove samples outside mass/pT window
    if remove_mass_pt_window:
        feature_array = feature_array[(spec_array[:,0] > 40) & (spec_array[:,0] < 200) & (spec_array[:,1] > 300) & (spec_array[:,1] < 2000)]
        label_array = label_array[(spec_array[:,0] > 40) & (spec_array[:,0] < 200) & (spec_array[:,1] > 300) & (spec_array[:,1] < 2000)]

    # Leave out jets that are not QCD or Hbb
    feature_array = feature_array[np.sum(label_array,axis=1)==1]
    label_array = label_array[np.sum(label_array,axis=1)==1]

    h5file.close()
    return feature_array, label_array
