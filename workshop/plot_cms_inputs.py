"""Plot raw CMS HDF5 inputs before training, using the autoencoder YAML."""
import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import yaml

LABELS = {
    'MET_pt': r'$p_T^{\mathrm{miss}}$ [GeV]',
    'M3l': r'$m_{3\ell}$ [GeV]', 'Z_deltaR': r'$\Delta R(\ell_Z,\ell_Z)$',
    'Z_mass': r'$m_{\ell\ell}$ [GeV]', 'Lep_pt_sum': r'$\sum p_T^{\ell}$ [GeV]',
    'Z_pt': r'$p_T^Z$ [GeV]', 'Lep1Z_pt': r'$p_T^{\ell_{Z,1}}$ [GeV]',
    'Lep2Z_pt': r'$p_T^{\ell_{Z,2}}$ [GeV]',
    'Lep3W_pt': r'$p_T^{\ell_W}$ [GeV]', 'W_mt': r'$m_T(\ell_W,p_T^{\mathrm{miss}})$ [GeV]'}
COLORS = {'DYJets': '#4169b2', 'WZ': '#d18b21', 'ZZ': '#008c82', 'Wprime': '#c32b64'}


def load_groups(config):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ml_training'))
    from src.autoencoder import _load_events, _split_by_process
    data, split = config['data'], config['anomaly_detection']
    features = data['features']
    normal, ids = _load_events(data['normal_input_paths'], features, data['label'],
                               data['normal_labels'], return_labels=True)
    (train, _, _), (train_ids, _, _) = _split_by_process(
        normal, ids, split['validation_fraction'], split['test_fraction'], split['seed'])
    names = {int(k): v for k, v in data['normal_process_names'].items()}
    groups = {names[int(pid)]: train[train_ids == pid] for pid in sorted(np.unique(train_ids))}
    groups['Wprime'] = _load_events(data['anomaly_input_paths'], features,
                                   data['label'], data['anomaly_labels'])
    return groups


def draw(ax, feature, index, groups, bins=40):
    values = np.concatenate([a[:, index] for a in groups.values()])
    low, high = float(values.min()), float(values.max())
    if low == high:
        low, high = low - 0.5, high + 0.5
    edges = np.linspace(low, high, bins + 1)
    for name, array in groups.items():
        counts, _ = np.histogram(array[:, index], bins=edges)
        density = counts / (len(array) * np.diff(edges))
        color = COLORS[name]
        if name != 'Wprime':
            ax.stairs(density, edges, fill=True, color=color, alpha=0.07)
        ax.stairs(density, edges, color=color, linewidth=2.2,
                  linestyle='--' if name == 'Wprime' else '-',
                  label=f'{"W′ (evaluación)" if name == "Wprime" else name} · {len(array):,}')
    ax.set_xlabel(LABELS.get(feature, feature))
    ax.set_ylabel('Densidad por proceso')
    ax.set_title(feature, loc='left', fontsize=11, color='#52667c', pad=10)
    ax.set_ylim(bottom=0)
    ax.tick_params(which='both', direction='in', top=True, right=True)
    ax.minorticks_on()
    ax.legend(frameon=False, fontsize=9)


def render(features, groups, output, config, bins=40):
    output = Path(output)
    if output.exists():
        raise FileExistsError(f'Use a new plot directory: {output}')
    if bins < 2 or not features or len(set(features)) != len(features):
        raise ValueError('Need distinct features and at least two bins')
    if set(groups) != set(COLORS):
        raise ValueError('Expected DYJets, WZ, ZZ and Wprime')
    for name, array in groups.items():
        if array.ndim != 2 or array.shape[1] != len(features) or not len(array) or not np.isfinite(array).all():
            raise ValueError(f'Invalid input array: {name}')
    output.mkdir(parents=True)
    with plt.rc_context({'font.size': 12, 'axes.labelsize': 13,
                         'axes.edgecolor': '#263b50', 'text.color': '#172f45',
                         'figure.facecolor': 'white', 'axes.facecolor': 'white',
                         'savefig.facecolor': 'white'}):
        def save(fig, stem):
            fig.suptitle('CMS Open Data · Simulación', x=0.08, ha='left',
                         fontsize=17, fontweight='bold')
            for ext in ('png', 'pdf', 'svg'):
                fig.savefig(output / f'{stem}.{ext}', dpi=200, bbox_inches='tight')
            plt.close(fig)
        for index, feature in enumerate(features):
            fig, ax = plt.subplots(figsize=(8, 6), layout='constrained')
            draw(ax, feature, index, groups, bins)
            save(fig, f'variable_{feature}')
        for stem, selected in [('variables_all', features),
                               ('variables_selected', [f for f in ('MET_pt', 'M3l', 'Z_pt', 'W_mt') if f in features])]:
            if not selected:
                continue
            rows = (len(selected) + 1) // 2
            fig, axes = plt.subplots(rows, 2, figsize=(14, 4.8 * rows),
                                     squeeze=False, layout='constrained')
            for ax, feature in zip(axes.flat, selected):
                draw(ax, feature, features.index(feature), groups, bins)
            for ax in list(axes.flat)[len(selected):]:
                ax.set_visible(False)
            save(fig, stem)
    (output / 'config.yaml').write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
    (output / 'sample_counts.json').write_text(json.dumps({
        'counts': {n: len(a) for n, a in groups.items()}, 'features': features,
        'SM_role': 'training split only; seed and fractions from YAML',
        'Wprime_role': 'evaluation only; no fitting',
        'normalization': 'unit area per process; full range, common bins; raw values before scaling',
        'bins': bins}, indent=2), encoding='utf-8')
    print(f'Gráficas guardadas en: {output}')


def plot_results(config, output, bins=40):
    render(config['data']['features'], load_groups(config), output, config, bins)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-f', '--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bins', type=int, default=40)
    args = parser.parse_args()
    plot_results(yaml.safe_load(args.config.read_text()), args.output, args.bins)
