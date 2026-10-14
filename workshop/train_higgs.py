"""Reproducible binary Higgs classification; test is opened only with --final."""
import argparse
import json
import os
from pathlib import Path
import platform

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

FORBIDDEN = {'EventId', 'Weight', 'Label', 'KaggleSet', 'KaggleWeight'}


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
    frame = pd.read_csv(os.path.expandvars(os.path.expanduser(data['input'])))
    frame, x, y, (train, val, test) = prepare(frame, data['features'], seed, int(data['max_events']))
    kind = settings['type']
    if kind == 'logistic':
        estimator = LogisticRegression(max_iter=int(settings['max_iter']), random_state=seed)
    elif kind == 'boosted':
        estimator = HistGradientBoostingClassifier(max_iter=int(settings['max_iter']),
                       learning_rate=float(settings.get('boosted_learning_rate', 0.1)), random_state=seed)
    elif kind == 'mlp':
        estimator = MLPClassifier(hidden_layer_sizes=tuple(settings['hidden_dims']),
            learning_rate_init=float(settings['learning_rate']), max_iter=int(settings['max_iter']),
            early_stopping=True, validation_fraction=0.15, random_state=seed)
    else:
        raise ValueError('model.type must be logistic, boosted or mlp')
    # Fit imputation and standardization ONLY on training. Missingness is informative.
    model = make_pipeline(SimpleImputer(strategy='median', add_indicator=True), StandardScaler(), estimator)
    model.fit(x[train], y[train])
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
        'roc_auc_unweighted': float(roc_auc_score(truth, scores)),
        'average_precision_unweighted': float(average_precision_score(truth, scores)),
        'threshold_from_validation': threshold, 'target_validation_background_acceptance': acceptance,
        'signal_efficiency': float(predicted[truth == 1].mean()),
        'background_acceptance': float(predicted[truth == 0].mean()),
        'counts': {'train': len(train), 'validation': len(val), 'test': len(test)},
        'confusion_matrix': confusion_matrix(truth, predicted).tolist(),
        'features': data['features'], 'seed': seed,
        'weighting': 'Unweighted pedagogical classification; AP is sample-dependent, not physical purity',
        'versions': {'python': platform.python_version(), 'sklearn': sklearn.__version__, 'numpy': np.__version__}}
    output.mkdir(parents=True)
    (output / 'config.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
    (output / 'metrics.json').write_text(json.dumps(metrics, indent=2))
    joblib.dump({'pipeline': model, 'features': data['features'], 'threshold': threshold}, output / 'model.joblib')
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
    for label, name in ((0, 'Background'), (1, 'Higgs')):
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
