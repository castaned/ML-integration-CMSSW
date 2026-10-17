"""Explore ATLAS training variables with the same YAML used to train the network."""
import argparse
import json
import numpy as np
import pandas as pd
import yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from train_atlas import METADATA, expanded


# Physical labels for the representative observables; other features retain their names.
LABELS = {
    'PRI_met': (r'$E_{T}^{\mathrm{miss}}$ [GeV]', 'Momento transversal faltante'),
    'PRI_tau_pt': (r'$p_{T}(\tau_{\mathrm{had}})$ [GeV]', 'Tau hadrónico'),
    'PRI_lep_pt': (r'$p_{T}(\ell)$ [GeV]', 'Electrón o muón'),
    'PRI_jet_leading_pt': (r'$p_{T}(j_1)$ [GeV]', 'Jet de mayor momento transversal'),
    'DER_mass_MMC': (r'$m_{\mathrm{MMC}}$ [GeV]', 'Masa estimada del candidato Higgs'),
    'DER_mass_transverse_met_lep': (r'$m_{T}(\ell, E_{T}^{\mathrm{miss}})$ [GeV]', 'Masa transversal leptón–MET'),
    'DER_mass_vis': (r'$m_{\mathrm{vis}}(\ell,\tau_{\mathrm{had}})$ [GeV]', 'Masa visible leptón–tau'),
    'DER_deltar_tau_lep': (r'$\Delta R(\ell,\tau_{\mathrm{had}})$', 'Separación angular leptón–tau'),
}
REPRESENTATIVE = list(LABELS)
STYLE = {
    'font.family': 'DejaVu Sans', 'font.size': 13,
    'axes.labelsize': 15, 'axes.linewidth': 1.2,
    'xtick.labelsize': 12, 'ytick.labelsize': 12,
    'xtick.direction': 'in', 'ytick.direction': 'in',
    'xtick.top': True, 'ytick.right': True,
    'xtick.major.size': 6, 'ytick.major.size': 6,
    'savefig.facecolor': 'white', 'figure.facecolor': 'white',
    'axes.spines.top': True, 'axes.spines.right': True,
}


def draw(ax, feature, values, bins):
    for name, color, linestyle in [('Fondo', '#2463a6', '-'),
                                   ('Higgs', '#c73937', '--')]:
        array = values[name]
        if len(array):
            counts, _ = np.histogram(array, bins=bins)
            ax.stairs(counts / (len(array) * np.diff(bins)), bins,
                      linewidth=2.5, color=color, linestyle=linestyle,
                      label=name)
    label, title = LABELS.get(feature, (feature, feature))
    ax.set(xlabel=label, ylabel='Densidad normalizada', xlim=(bins[0], bins[-1]), ylim=(0, None))
    ax.text(0, 1.13, title, transform=ax.transAxes, fontsize=15, fontweight='bold')
    ax.text(0, 1.035, 'Higgs Challenge · Simulación', transform=ax.transAxes, fontsize=11)
    ax.text(0, -.25, feature, transform=ax.transAxes, fontsize=10, color='#526778')
    ax.legend(frameon=False, fontsize=12, loc='upper right')
    ax.minorticks_on()
    ax.tick_params(which='minor', direction='in', top=True, right=True)


def run(config):
    frame=pd.read_csv(expanded(config['data']['input']))
    frame=frame.loc[frame.KaggleSet=='t'].copy()
    features=config['data']['features']
    if features=='all_physics': features=[c for c in frame if c.startswith(('PRI_','DER_'))]
    if not isinstance(features,list) or not features or len(features)!=len(set(features)) or METADATA.intersection(features) or not set(features)<=set(frame):
        raise ValueError('Invalid physics feature list')
    options=config.get('plots',{})
    out=expanded(options.get('directory','$HOME/hep-workshop/plots/atlas_inputs01'))
    if out.exists(): raise FileExistsError(f'Use a new plots.directory: {out}')
    out.mkdir(parents=True)
    plt.rcParams.update(STYLE)
    statistics=[]
    with PdfPages(out/'input_variables.pdf') as pdf:
        for start in range(0,len(features),4):
            fig,axes=plt.subplots(2,2,figsize=(13,11))
            for ax,feature in zip(axes.flat,features[start:start+4]):
                values={}
                for label,name in [('b','Fondo'),('s','Higgs')]:
                    array=frame.loc[frame.Label==label,feature].to_numpy(dtype=float)
                    valid=np.isfinite(array)&(array!=config['data']['missing_value'])
                    values[name]=array[valid]
                    statistics.append({'feature':feature,'class':name,'events':len(array),
                                       'missing_fraction':float(1-valid.mean())})
                present=[v for v in values.values() if len(v)]
                if not present: raise ValueError(f'{feature}: no available values')
                quantile=float(options.get('upper_quantile',0.995))
                if not 0.5<quantile<=1:raise ValueError('upper_quantile must be in (0.5, 1]')
                low=min(v.min() for v in present);high=max(np.quantile(v,quantile) for v in present)
                if low==high:low,high=low-.5,high+.5
                bins=np.linspace(low,high,int(options.get('bins',40))+1)
                draw(ax, feature, values, bins)
                if feature in REPRESENTATIVE:
                    single, single_ax = plt.subplots(figsize=(7.5, 6.5))
                    draw(single_ax, feature, values, bins)
                    single.subplots_adjust(left=.16, right=.97, bottom=.22, top=.82)
                    single.savefig(out/f'{feature}.png', dpi=190)
                    single.savefig(out/f'{feature}.pdf')
                    single.savefig(out/f'{feature}.svg')
                    plt.close(single)
            for ax in list(axes.flat)[len(features[start:start+4]):]: ax.set_visible(False)
            fig.subplots_adjust(left=.09, right=.98, bottom=.12, top=.86, hspace=.65, wspace=.3)
            fig.suptitle('CERN Open Data · ATLAS Higgs Challenge', fontsize=18, fontweight='bold', y=.98)
            fig.text(.5, .935, 'Muestra de entrenamiento · Formas sin pesos de evento', ha='center', fontsize=12)
            fig.text(.5,.018,'Valores ausentes excluidos · Normalización antes del recorte de colas',ha='center',fontsize=11)
            pdf.savefig(fig)
            fig.savefig(out/f'variables_{start//4+1:02d}.png',dpi=180)
            fig.savefig(out/f'variables_{start//4+1:02d}.svg')
            plt.close(fig)
    pd.DataFrame(statistics).to_csv(out/'variable_summary.csv',index=False)
    (out/'config.yaml').write_text(yaml.safe_dump(config,sort_keys=False))
    (out/'sample_counts.json').write_text(json.dumps(frame.Label.value_counts().to_dict(),indent=2))
    print('Variable plots:',out)
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('-f','--config',required=True)
    a=p.parse_args();run(yaml.safe_load(expanded(a.config).read_text()))
