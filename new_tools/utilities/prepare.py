# Script to prepare data to train IA models
import tables
import numpy as np
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
import h5py
from torch.utils.data import random_split
import yaml
import os

def load_config(config_path):
    with open(config_path) as f:
        return yaml.safe_load(f)
    
class h5Dataset(Dataset):
    def __init__(self, dir_paths, features, label, num_classes, indices=None, transform=None):
        
        self.features = features
        self.num_features = len(features)
        self.label = label
        self.num_classes = num_classes
        self.transform = transform
        
        self.file_paths = []
        self.file_event_counts = []
        
        for dir_path in dir_paths:
            for file_name in sorted(os.listdir(dir_path)):
                if file_name.endswith(".h5"):
                    file_path = os.path.join(dir_path, file_name)
                    self.file_paths.append(file_path)
                    
                    # All features must have same number of events
                    with h5py.File(file_path, "r") as file_h5:
                        n_events = file_h5[features[0]].shape[0]
                    self.file_event_counts.append(n_events)
                        
        self.files = [None] * len(self.file_paths) # Lazy open, one handle per worker
        
        self.global_ids = []
        for file_id, n_events in enumerate(self.file_event_counts):
            for event_id in range(n_events):
                self.global_ids.append((file_id, event_id))
                
        if indices is not None:
            self.global_ids = indices
                                    
    def __len__(self):
        return len(self.global_ids)
        
    def __getitem__(self, idx):
        file_id, event_id = self.global_ids[idx]
        
        # Lazy open H5 files
        if self.files[file_id] is None:
            self.files[file_id] = h5py.File(self.file_paths[file_id], "r")
        file_h5 = self.files[file_id]
            
        x = [file_h5[feature][event_id][...] for feature in self.features]
        x = {f: torch.tensor(x[i], dtype=torch.float32) for i, f in enumerate(self.features)}
        
        y = torch.tensor(file_h5[self.label][event_id], dtype=torch.long)
        y = (y - 1).long()
        
        if self.transform:
            x = self.transform(x)
            
        return x, y
                
    def close(self):
        for file in self.files:
            if file:
                file.close()

class MLPTransform:
    def __call__(self, data):
        flatten = torch.cat([value.flatten() for value in data.values()])
        return flatten


def split_and_transform_pythorch(h5_dataset, test_size, batch_size, train_suffle=True):

    test_len = int(test_size * len(h5_dataset))
    train_len  = len(h5_dataset) - test_len
    train_set, test_set = random_split(h5_dataset, [train_len, test_len])
    
    train_dataloader = DataLoader(train_set, batch_size=batch_size, shuffle=train_suffle)
    test_dataloader = DataLoader(test_set, batch_size=batch_size)
    
    return train_dataloader, test_dataloader


def split_h5Dataset(dataset, test_size, seed):
    all_indices = list(range(len(dataset)))

    train_idx, test_idx = train_test_split(
            all_indices,
            test_size=test_size,
            random_state=seed,
            shuffle=True,
        )
    return train_idx, test_idx
