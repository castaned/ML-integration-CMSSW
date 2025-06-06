# Script to prepare data to train IA models
import tables
import numpy as np
import utilities.read_config_variables as rcv
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import DataLoader, TensorDataset
import onnx


def clean_array_values(array):

    cleaned = []
    for value in array:
        if isinstance(value, (np.integer, int)):
            cleaned.append(int(value))
        elif isinstance(value, (np.float64, float)) and value.is_integer():
            cleaned.append(int(value))
        else:
            cleaned.append(value)

    return np.array(cleaned, dtype=object)

def onehot(label_array, outdir):

    unique_classes = np.unique(label_array)
    indices = np.searchsorted(unique_classes, label_array.flatten())
    onehot_encoder = np.eye(len(unique_classes))[indices]

    np.save(f"{outdir}/label_decoder.npy", unique_classes)        
    
    return onehot_encoder

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

def convert_to_onnx(X, model, output_dir, model_name):

    dummy_input = torch.randn(1, X.shape[1], dtype=torch.float32)
    torch.onnx.export(
        model,
        dummy_input,
        f"{output_dir}/best_model_{model_name}.onnx",
        export_params=True,
        opset_version=12,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
    'input': {0: 'batch_size'},
    'output': {0: 'batch_size'}
        }
    )

    # Verify
    onnx.checker.check_model(onnx.load(f"{output_dir}/best_model_{model_name}.onnx"))
    return 0

def combine_features_labels(file_vars, fn, params=None, test=False):
    
    # Get variables
    combined_features, combined_labels = None, None
    type_path = 'test_path' if test else 'train_path'    
    file_paths = rcv.read_variables(file_vars, [type_path])[type_path]

    # Compute function and combine outputs
    for file_path in file_paths:
        features, labels = fn(file_path, file_vars, **params or {})
        
        if combined_labels is None:
            combined_features = features
            combined_labels = labels
        else:
            try:
                combined_features = np.vstack((combined_features, features))
                combined_labels = np.concatenate((combined_labels, labels))
            except ValueError as e:
                raise ValueError(f"Shape mismatch when combining arrays from {file_path}: {str(e)}")

    return combined_features, combined_labels

def get_features_labels(file_name, file_vars):

    variables = rcv.read_variables(file_vars, ['features', 'labels', 'output_path'])
    #print(variables)
    output_dir = variables['output_path'][0]
    features = variables['features']
    labels = variables['labels']
    #print(file_name)
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
        
    #label_array = (label_array == 2).astype(int)
    #if label_array.shape[1] == 1:
    #    label_array = np.eye(2)[label_array.flatten()] # Onehot encoder
    ## Leave out events that are not either or both
    #feature_array = feature_array[np.sum(label_array,axis=1)==1]
    #label_array = label_array[np.sum(label_array,axis=1)==1]

    onehot_label_array = onehot(label_array, output_dir)

    h5file.close()
    return feature_array, onehot_label_array



# def oldget_features_labels(file_vars, remove_mass_pt_window=True, test=False):

#     # Get variables
#     if test:
#         file_path = 'test_path'
#     else:
#         file_path = 'train_path'

#     variables = rcv.read_variables(file_vars, [file_path, 'features', 'spectators', 'labels'])
#     #print(variables)
#     file_name = variables[file_path][0] 
#     features = variables['features']
#     spectators = variables['spectators']
#     labels = variables['labels']

#     nfeatures = len(features)
#     nspectators = len(spectators)
#     nlabels = len(labels)

#     # load file
#     h5file = tables.open_file(file_name, 'r')
#     njets = getattr(h5file.root,features[0]).shape[0]

#     # allocate arrays
#     feature_array = np.zeros((njets,nfeatures))
#     spec_array = np.zeros((njets,nspectators))
#     label_array = np.zeros((njets,nlabels))

#     # load arrays
#     for (i, feat) in enumerate(features):
#         feature_array[:,i] = getattr(h5file.root,feat)[:]

#     for (i, spec) in enumerate(spectators):
#         spec_array[:,i] = getattr(h5file.root,spec)[:]

#     for (i, label) in enumerate(labels):
#         prods = label.split('*')
#         prod0 = prods[0]
#         prod1 = prods[1]
#         fact0 = getattr(h5file.root,prod0)[:]
#         fact1 = getattr(h5file.root,prod1)[:]
#         label_array[:,i] = np.multiply(fact0,fact1)

#     # remove samples outside mass/pT window
#     if remove_mass_pt_window:
#         feature_array = feature_array[(spec_array[:,0] > 40) & (spec_array[:,0] < 200) & (spec_array[:,1] > 300) & (spec_array[:,1] < 2000)]
#         label_array = label_array[(spec_array[:,0] > 40) & (spec_array[:,0] < 200) & (spec_array[:,1] > 300) & (spec_array[:,1] < 2000)]

#     # Leave out jets that are not QCD or Hbb
#     feature_array = feature_array[np.sum(label_array,axis=1)==1]
#     label_array = label_array[np.sum(label_array,axis=1)==1]

#     h5file.close()
#     return feature_array, label_array
