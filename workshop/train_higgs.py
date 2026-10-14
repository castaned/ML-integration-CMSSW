"""Reproducible binary Higgs classification; test is opened only with --final."""
import argparse
import json
import os
from pathlib import Path
import platform
import time
import sys

import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve, average_precision_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import yaml
from event_io import read_events_h5
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ml_training.utilities.labels import normalize_class_id_map,encode_label,remap_class_names

FORBIDDEN = {'EventId', 'Dataset_ID', 'Weight', 'Label', 'KaggleSet', 'KaggleWeight'}


def dataset_labels(frame,data):
    label=data.get('label','Dataset_ID' if 'Dataset_ID' in frame else 'Label')
    if label=='Label':return frame,{}
    if int(data.get('num_classes',2))!=2:raise ValueError('This workshop classifier is binary')
    mapping=normalize_class_id_map(data['class_id_map'],2)
    path=Path(os.path.expandvars(os.path.expanduser(data['label_mapping'])))
    names={int(key):value for key,value in json.loads(path.read_text()).items()}
    embedded=frame.attrs.get('dataset_map')
    if embedded is not None and {int(k):v for k,v in embedded.items()}!=names:
        raise ValueError('External dataset_map disagrees with the map stored in HDF5')
    if not set(mapping)<=set(names):raise ValueError('class_id_map contains IDs absent from dataset_map')
    raw=frame[label].to_numpy()
    if not np.isfinite(raw).all() or np.any(raw!=raw.astype(np.int64)):
        raise ValueError('Dataset_ID must contain integer identifiers')
    if not set(np.unique(raw))<=set(names):raise ValueError('Dataset_ID absent from dataset_map')
    encoded=np.array([encode_label(value,2,mapping) for value in raw])
    frame=frame.copy()
    frame['Label']=np.where(encoded==1,'s','b')
    return frame,remap_class_names({key:names[key] for key in mapping},mapping)


def prepare(frame, features, seed, max_events):
    if not features or len(features) != len(set(features)) or FORBIDDEN.intersection(features):
        raise ValueError('Choose unique physical features; IDs, labels and weights are forbidden')
    if any(not f.startswith(('PRI_', 'DER_')) for f in features):
        raise ValueError('Only documented PRI_/DER_ observables may be inputs')
    if not frame.EventId.is_unique or not set(frame.Label.unique()) <= {'s', 'b'}:
        raise ValueError('Duplicate events or unknown labels')
    if set(frame.Label.unique()) != {'s', 'b'}:
        raise ValueError('Both signal and background required')
    # Reproducible random subset; do not take the first N potentially ordered rows.
    if max_events and len(frame) > max_events:
        frame, _ = train_test_split(frame, train_size=max_events, stratify=frame.Label, random_state=seed)
    x = frame[features].replace(-999, np.nan).to_numpy(dtype=float)
    if np.isinf(x).any():
        raise ValueError('Infinite observable')
    y = (frame.Label == 's').to_numpy(dtype=int)
    indices = np.arange(len(frame))
    train, held = train_test_split(indices, test_size=0.4, stratify=y, random_state=seed)
    validation, test = train_test_split(held, test_size=0.5, stratify=y[held], random_state=seed)
    if np.isnan(x[train]).all(axis=0).any():
        raise ValueError('A feature is entirely missing in training')
    return frame, x, y, (train, validation, test)


def run(config, output, final=False):
    output = Path(output).expanduser()
    if output.exists():
        raise FileExistsError('Use a new output directory for each experiment')
    data, settings = config['data'], config['model']
    seed = int(config['split']['seed'])
    input_path=Path(os.path.expandvars(os.path.expanduser(data['input'])))
    frame = read_events_h5(input_path) if input_path.suffix.lower() in ('.h5','.hdf5') else pd.read_csv(input_path)
    frame,class_names=dataset_labels(frame,data)
    frame, x, y, (train, val, test) = prepare(frame, data['features'], seed, int(data['max_events']))
    if any(np.count_nonzero(y[part] == label) < 20 for part in (val,test) for label in (0,1)):
        raise ValueError('Fewer than 20 events of a class in validation/test. Process more NanoAOD before training.')
    kind = settings['type']
    if kind == 'logistic':
        estimator = LogisticRegression(max_iter=int(settings['max_iter']), random_state=seed)
    elif kind == 'boosted':
        estimator = HistGradientBoostingClassifier(max_iter=int(settings['max_iter']),
                       learning_rate=float(settings.get('boosted_learning_rate', 0.1)), random_state=seed)
    elif kind == 'mlp':
        estimator = MLPClassifier(hidden_layer_sizes=tuple(settings['hidden_dims']),
            learning_rate_init=float(settings['learning_rate']), max_iter=int(settings['max_iter']),
            batch_size=int(settings.get('batch_size', 128)),
            early_stopping=True, validation_fraction=0.15, random_state=seed)
    else:
        raise ValueError('model.type must be logistic, boosted or mlp')
    # Fit imputation and standardization ONLY on training. Missingness is informative.
    model = make_pipeline(SimpleImputer(strategy='median', add_indicator=True), StandardScaler(), estimator)
    started = time.perf_counter()
    model.fit(x[train], y[train])
    fit_seconds = time.perf_counter() - started
    val_score = model.predict_proba(x[val])[:, 1]
    acceptance = float(config['evaluation']['background_acceptance'])
    if not 0 < acceptance < 1:
        raise ValueError('background_acceptance must be between zero and one')
    threshold = float(np.quantile(val_score[y[val] == 0], 1 - acceptance))
    indices = test if final else val
    scores = model.predict_proba(x[indices])[:, 1]
    truth = y[indices]
    predicted = scores >= threshold
    metrics = {'evaluation_set': 'test' if final else 'validation', 'model': kind,
        'fit_seconds': fit_seconds, 'iterations_run': int(np.max(getattr(estimator, 'n_iter_', 0))),
        'roc_auc_unweighted': float(roc_auc_score(truth, scores)),
        'average_precision_unweighted': float(average_precision_score(truth, scores)),
        'threshold_from_validation': threshold, 'target_validation_background_acceptance': acceptance,
        'signal_efficiency': float(predicted[truth == 1].mean()),
        'background_acceptance': float(predicted[truth == 0].mean()),
        'counts': {'train': len(train), 'validation': len(val), 'test': len(test)},
        'confusion_matrix': confusion_matrix(truth, predicted).tolist(),
        'features': data['features'], 'seed': seed,
        'class_names':class_names,'class_id_map':data.get('class_id_map'),
        'weighting': 'Unweighted pedagogical classification; AP is sample-dependent, not physical purity',
        'versions': {'python': platform.python_version(), 'sklearn': sklearn.__version__, 'numpy': np.__version__}}
    output.mkdir(parents=True)
    (output / 'config.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
    (output / 'metrics.json').write_text(json.dumps(metrics, indent=2))
    if class_names:
        import shutil
        shutil.copy2(os.path.expandvars(os.path.expanduser(data['label_mapping'])),output/'dataset_map.json')
    joblib.dump({'pipeline': model, 'features': data['features'], 'threshold': threshold,
                 'class_names':class_names,'class_id_map':data.get('class_id_map')}, output / 'model.joblib')
    # Keep event IDs to make splits auditable without including IDs in model inputs.
    split_names = np.empty(len(frame), dtype=object)
    for name, part in zip(('train', 'validation', 'test'), (train, val, test)):
        split_names[part] = name
    pd.DataFrame({'EventId': frame.EventId.to_numpy(), 'split': split_names}).to_csv(output / 'splits.csv', index=False)
    pd.DataFrame({'EventId': frame.EventId.to_numpy()[indices], 'label': truth, 'score': scores}).to_csv(output / 'scores.csv', index=False)
    fpr, tpr, _ = roc_curve(truth, scores)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(fpr, tpr, label=f"AUC {metrics['roc_auc_unweighted']:.3f}")
    axes[0].plot([0, 1], [0, 1], '--', color='gray')
    axes[0].set(xlabel='Background acceptance', ylabel='Higgs efficiency', title=metrics['evaluation_set'])
    axes[0].legend()
    for label, name in ((0, class_names.get(0,'Background')), (1, class_names.get(1,'Higgs'))):
        axes[1].hist(scores[truth == label], bins=np.linspace(0, 1, 31), density=True, histtype='step', label=name)
    axes[1].axvline(threshold, color='black', linestyle='--', label='Validation threshold')
    axes[1].set(xlabel='Classifier score', ylabel='Unit-area density')
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(output / 'classification.pdf')
    fig.savefig(output / 'classification.png', dpi=180)
    plt.close(fig)
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('-f', '--config', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--final', action='store_true', help='Instructor-authorized final evaluation after freezing choices')
    a = p.parse_args()
    run(yaml.safe_load(Path(a.config).read_text()), a.output, a.final)
