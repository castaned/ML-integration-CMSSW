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
                        if features == "all" or features == ["all"]:
                            self.features = [key for key in file_h5.keys() if key != label]
                        n_events = file_h5[self.features[0]].shape[0]
                    self.file_event_counts.append(n_events)

        self.num_features = len(self.features)
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
        
        if self.transform:
            x = self.transform(x)
            
        return x, y

    def __getitems__(self, indices):
        by_file = {}
        for pos, idx in enumerate(indices):
            file_id, event_id = self.global_ids[idx]
            by_file.setdefault(file_id, []).append((event_id, pos))

        results = [None] * len(indices)

        for file_id, pairs in by_file.items():
            # h5py fancy indexing requires ascending, unique order
            pairs.sort(key=lambda p: p[0])
            event_ids = [p[0] for p in pairs]
            positions = [p[1] for p in pairs]

            if self.files[file_id] is None:
                self.files[file_id] = h5py.File(self.file_paths[file_id], "r")
            file_h5 = self.files[file_id]

            feat_arrays = {f: file_h5[f][event_ids] for f in self.features}
            label_array = file_h5[self.label][event_ids]

            for i, pos in enumerate(positions):
                x = {f: torch.tensor(feat_arrays[f][i], dtype=torch.float32) for f in self.features}
                y = torch.tensor(label_array[i], dtype=torch.long)
                if self.transform:
                    x = self.transform(x)
                results[pos] = (x, y)

        return results

    def close(self):
        for file in self.files:
            if file:
                file.close()


def split_and_transform_pythorch(h5_dataset, test_size, batch_size, train_suffle=True):

    test_len = int(test_size * len(h5_dataset))
    train_len  = len(h5_dataset) - test_len
    train_set, test_set = random_split(h5_dataset, [train_len, test_len])
    
    train_dataloader = DataLoader(
        train_set, batch_size=batch_size, shuffle=train_suffle,
        num_workers=4, pin_memory=True, persistent_workers=True,
    )
    test_dataloader = DataLoader(
        test_set, batch_size=batch_size,
        num_workers=2, pin_memory=True, persistent_workers=True,
    )
    
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
