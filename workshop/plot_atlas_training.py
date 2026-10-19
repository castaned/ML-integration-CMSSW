"""Export individual training figures from saved ATLAS results; no retraining."""
import argparse
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator, AutoMinorLocator
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve


def plot_results(directory):
    out = Path(os.path.expandvars(os.path.expanduser(str(directory))))
    history = pd.read_csv(out / 'history.csv')
    scores = pd.read_csv(out / 'validation_scores.csv')
    metrics = json.loads((out / 'metrics.json').read_text())
    style = {'font.size': 14, 'axes.labelsize': 16, 'legend.fontsize': 12,
             'xtick.labelsize': 12, 'ytick.labelsize': 12, 'axes.linewidth': 1.2,
             'xtick.direction': 'in', 'ytick.direction': 'in',
             'xtick.top': True, 'ytick.right': True, 'savefig.facecolor': 'white'}
    paths = []
    with plt.rc_context(style):
        for name in ('training_loss', 'roc_curve', 'classifier_scores'):
            fig, ax = plt.subplots(figsize=(8, 6.5), layout='constrained')
            ax.tick_params(which='major', length=7)
            ax.tick_params(which='minor', length=4)
            ax.xaxis.set_minor_locator(AutoMinorLocator())
            ax.yaxis.set_minor_locator(AutoMinorLocator())
            ax.text(0, 1.07, 'ATLAS Higgs Challenge', transform=ax.transAxes,
                    fontsize=16, fontweight='bold')
            ax.text(0, 1.02, 'Simulación · Validación interna', transform=ax.transAxes,
                    fontsize=12, color='#536777')
            if name == 'training_loss':
                ax.plot(history.epoch, history.train_loss, color='#2463a6', lw=2.3,
                        marker='o', ms=3, label='Entrenamiento')
                ax.plot(history.epoch, history.validation_loss, color='#c73937', lw=2.3,
                        ls='--', marker='s', ms=3, label='Validación')
                ax.axvline(metrics['best_epoch'], color='#00878a', lw=1.5, ls=':',
                           label=f"Mejor época: {metrics['best_epoch']}")
                ax.set(xlabel='Época', ylabel='Pérdida (BCE)')
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))
                ax.legend(frameon=False)
            elif name == 'roc_curve':
                fpr, tpr, _ = roc_curve(scores.label, scores.score)
                ax.plot(fpr, tpr, lw=2.5, color='#2463a6',
                        label=f"AUC = {metrics['roc_auc_unweighted']:.4f}")
                ax.plot([0, 1], [0, 1], color='#7d8994', ls='--', lw=1.3,
                        label='Clasificación aleatoria')
                ax.set(xlabel='Aceptación de fondo', ylabel='Eficiencia de señal',
                       xlim=(0, 1), ylim=(0, 1.02))
                ax.legend(loc='lower right', frameon=False)
            else:
                for label, title, color, ls in ((0, 'Fondo', '#2463a6', '-'),
                                               (1, 'Higgs → ττ', '#c73937', '--')):
                    ax.hist(scores.loc[scores.label == label, 'score'],
                            bins=np.linspace(0, 1, 41), density=True,
                            histtype='step', lw=2.3, color=color, ls=ls, label=title)
                ax.set(xlabel='Puntuación del clasificador',
                       ylabel='Densidad normalizada por clase', xlim=(0, 1))
                ax.legend(frameon=False)
            for ext in ('png', 'pdf', 'svg'):
                path = out / f'{name}.{ext}'
                fig.savefig(path, dpi=220)
                paths.append(path)
            plt.close(fig)
    return paths


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', required=True)
    for path in plot_results(parser.parse_args().results):
        print(path)
