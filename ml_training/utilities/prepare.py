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
                
    def close(self):
        for idx, file in enumerate(self.files):
            if file:
                file.close()
                self.files[idx] = None

    def get_all_labels(self):
        labels = []
        opened_files = {}
        try:
            for file_id, event_id in self.global_ids:
                if file_id not in opened_files:
                    opened_files[file_id] = h5py.File(self.file_paths[file_id], "r")
                labels.append(int(opened_files[file_id][self.label][event_id]))
        finally:
            for handle in opened_files.values():
                handle.close()
        return np.asarray(labels, dtype=int)

    def filter_global_ids_by_labels(self, accepted_labels):
        accepted_labels = set(int(label) for label in accepted_labels)
        labels = self.get_all_labels()
        return [self.global_ids[idx] for idx, label in enumerate(labels) if label in accepted_labels]


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


def split_global_ids(global_ids, test_size, seed):
    if not global_ids:
        return [], []

    if test_size <= 0:
        return list(global_ids), []
    if test_size >= 1:
        return [], list(global_ids)

    train_ids, test_ids = train_test_split(
        list(global_ids),
        test_size=test_size,
        random_state=seed,
        shuffle=True,
    )
    return list(train_ids), list(test_ids)


def build_autoencoder_splits(dataset, normal_labels, anomaly_labels, val_size, test_size, seed):
    if val_size < 0 or test_size < 0 or (val_size + test_size) >= 1:
        raise ValueError("val_size and test_size must be >= 0 and their sum must be < 1")

    normal_ids = dataset.filter_global_ids_by_labels(normal_labels)
    anomaly_ids = dataset.filter_global_ids_by_labels(anomaly_labels)

    if not normal_ids:
        raise ValueError("No events found for the requested normal_labels")
    if not anomaly_ids:
        raise ValueError("No events found for the requested anomaly_labels")

    heldout_fraction = val_size + test_size
    train_normal_ids, heldout_normal_ids = split_global_ids(normal_ids, heldout_fraction, seed)

    if not heldout_normal_ids:
        raise ValueError("No normal events left for validation/testing after the split")

    if heldout_fraction == 0:
        val_normal_ids, test_normal_ids = [], []
    else:
        test_fraction_inside_heldout = test_size / heldout_fraction if heldout_fraction > 0 else 0
        val_normal_ids, test_normal_ids = split_global_ids(heldout_normal_ids, test_fraction_inside_heldout, seed + 1)

    if heldout_fraction == 0:
        val_anomaly_ids, test_anomaly_ids = [], []
    else:
        test_fraction_inside_heldout = test_size / heldout_fraction if heldout_fraction > 0 else 0
        val_anomaly_ids, test_anomaly_ids = split_global_ids(anomaly_ids, test_fraction_inside_heldout, seed + 2)

    rng = np.random.default_rng(seed)
    val_ids = list(val_normal_ids) + list(val_anomaly_ids)
    test_ids = list(test_normal_ids) + list(test_anomaly_ids)
    rng.shuffle(val_ids)
    rng.shuffle(test_ids)

    return {
        "train_normal": list(train_normal_ids),
        "val_normal": list(val_normal_ids),
        "val_mixed": val_ids,
        "test_mixed": test_ids,
    }
