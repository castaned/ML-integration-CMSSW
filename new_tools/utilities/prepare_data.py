# Script to prepare data to train IA models
import tables
import numpy as np
from utilities.read_config_variables import read_variables
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import DataLoader, TensorDataset

def train_data_to_pytorch(X, y, val_split, batch_size):
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=val_split, shuffle=True)

    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_train_tensor = torch.argmax(torch.tensor(y_train, dtype=torch.long), dim=1)
    X_val_tensor = torch.tensor(X_val, dtype=torch.float32)
    y_val_tensor = torch.argmax(torch.tensor(y_val, dtype=torch.long), dim=1)

    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    val_dataset = TensorDataset(X_val_tensor, y_val_tensor)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader

def oldget_features_labels(file_vars, remove_mass_pt_window=True, test=False):

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


def get_features_labels(file_vars, test=False):

    # Get variables
    if test:
        file_path = 'test_path'
    else:
        file_path = 'train_path'

    variables = read_variables(file_vars, [file_path, 'features', 'labels'])
    print(variables)
    file_name = variables[file_path][0] 
    features = variables['features']
    labels = variables['labels']
    print(file_name)
    nfeatures = len(features)
    nlabels = len(labels)

    # load file
    h5file = tables.open_file(file_name, 'r')
    njets = getattr(h5file.root,features[0]).shape[0]

    # allocate arrays
    feature_array = np.zeros((njets,nfeatures))
    label_array = np.zeros((njets,nlabels))

    # load labels arrays
    for (i, label) in enumerate(labels):
        label_array[:,i] = getattr(h5file.root,label)[:]
        
    label_array = (label_array == 2).astype(int)
    if label_array.shape[1] == 1:
        label_array = np.eye(2)[label_array.flatten()] # Onehot encoder

    # Leave out events that are not either or both
    feature_array = feature_array[np.sum(label_array,axis=1)==1]
    label_array = label_array[np.sum(label_array,axis=1)==1]

    h5file.close()
    return feature_array, label_array

