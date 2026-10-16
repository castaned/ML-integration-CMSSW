"""Compare selected Higgs/ZZ input shapes, using the training YAML and existing HDF5."""
import argparse
import json
import math
import os
from pathlib import Path
import numpy as np
import yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from event_io import read_events_h5

LABELS = {
    'DER_m4l': r'$m_{4\ell}$', 'DER_mZ1': r'$m_{Z_1}$', 'DER_mZ2': r'$m_{Z_2}$',
    'DER_pt4l': r'$p_T(4\ell)$', 'DER_ptZ1': r'$p_T(Z_1)$', 'DER_ptZ2': r'$p_T(Z_2)$',
    'DER_sum_lepton_pt': r'$\sum p_T(\ell)$', 'PRI_met': r'$p_T^{miss}$',
    **{f'PRI_lepton{i}_pt': rf'$p_T(\ell_{i})$' for i in range(1,5)}}


def plot_variables(frame, dataset_map, features, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError(f'Use a new plot directory: {output}')
    missing = set(features + ['Dataset_ID']) - set(frame.columns)
    if missing:
        raise ValueError(f'Missing input columns: {sorted(missing)}')
    if not features:
        raise ValueError('No input features')
    mapping = {int(k): str(v) for k,v in dataset_map.items()}
    if set(frame.Dataset_ID.unique()) - set(mapping):
        raise ValueError('Dataset IDs missing from dataset_map')
    output.mkdir(parents=True)
    columns = 3
    fig, axes = plt.subplots(math.ceil(len(features)/columns), columns,
                             figsize=(14, 3.5*math.ceil(len(features)/columns)), squeeze=False)
    stats = {}
    for axis, feature in zip(axes.flat, features):
        arrays = {identifier: np.asarray(frame.loc[frame.Dataset_ID == identifier,feature], dtype=float)
                  for identifier in mapping}
        arrays = {identifier: values[np.isfinite(values)] for identifier,values in arrays.items()}
        nonempty = [values for values in arrays.values() if len(values)]
        if not nonempty:
            raise ValueError(f'{feature}: no finite values')
        low = min(values.min() for values in nonempty)
        high = max(values.max() for values in nonempty)
        if low == high: low,high = low-0.5,high+0.5
        bins = np.linspace(low,high,41)
        stats[feature] = {mapping[k]: {'finite_events': len(v)} for k,v in arrays.items()}
        def draw(ax):
            for identifier, values in arrays.items():
                if len(values):
                    ax.hist(values,bins=bins,density=True,histtype='step',linewidth=1.8,
                            label=f'{mapping[identifier]} (N={len(values):,})')
            ax.set(xlabel=LABELS.get(feature,feature)+' [GeV]', ylabel='Unit-area density')
            ax.legend(fontsize=8);ax.grid(alpha=0.18)
        draw(axis)
        single, ax = plt.subplots(figsize=(6,4.5))
        draw(ax); single.tight_layout()
        for extension in ('png','pdf'):
            single.savefig(output/f'{feature}.{extension}',dpi=180)
        plt.close(single)
    for axis in list(axes.flat)[len(features):]: axis.set_visible(False)
    fig.suptitle('Higgs125 vs ZZ4L: selected input observables | shapes, not expected yields',fontsize=14)
    fig.tight_layout(rect=(0,0,1,0.97))
    for extension in ('png','pdf'): fig.savefig(output/f'input_variables.{extension}',dpi=180)
    plt.close(fig)
    (output/'plot_summary.json').write_text(json.dumps(stats,indent=2))
    return output


def run(config, output):
    data = config['data']
    expand = lambda p: Path(os.path.expandvars(os.path.expanduser(p)))
    frame = read_events_h5(expand(data['input']))
    mapping = json.loads(expand(data['label_mapping']).read_text())
    if frame.attrs.get('dataset_map') != {str(k):str(v) for k,v in mapping.items()}:
        raise ValueError('HDF5 and label_mapping disagree')
    result = plot_variables(frame,mapping,data['features'],output)
    (result/'config.yaml').write_text(yaml.safe_dump(config,sort_keys=False))
    print('Input comparison plots:',result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-f','--config',required=True)
    parser.add_argument('--output',required=True)
    args = parser.parse_args()
    run(yaml.safe_load(Path(args.config).expanduser().read_text()),args.output)
