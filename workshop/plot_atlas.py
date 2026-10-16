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
    statistics=[]
    with PdfPages(out/'input_variables.pdf') as pdf:
        for start in range(0,len(features),6):
            fig,axes=plt.subplots(2,3,figsize=(14,7))
            for ax,feature in zip(axes.flat,features[start:start+6]):
                values={}
                for label,name in [('b','Background'),('s','Higgs')]:
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
                for name,array in values.items():
                    if len(array):
                        counts,_=np.histogram(array,bins=bins)
                        ax.stairs(counts/(len(array)*np.diff(bins)),bins,linewidth=1.7,label=name)
                ax.set(xlabel=feature,ylabel='Unit-area density');ax.legend(fontsize=8);ax.grid(alpha=.15)
            for ax in list(axes.flat)[len(features[start:start+6]):]: ax.set_visible(False)
            fig.suptitle('ATLAS Higgs Challenge: training sample | signal and background shapes')
            fig.text(.5,.01,'Upper tails zoomed using per-class quantiles; density normalized before zoom',ha='center',fontsize=9)
            fig.tight_layout(rect=(0,.035,1,.96));pdf.savefig(fig)
            fig.savefig(out/f'variables_{start//6+1:02d}.png',dpi=150);plt.close(fig)
    pd.DataFrame(statistics).to_csv(out/'variable_summary.csv',index=False)
    (out/'config.yaml').write_text(yaml.safe_dump(config,sort_keys=False))
    (out/'sample_counts.json').write_text(json.dumps(frame.Label.value_counts().to_dict(),indent=2))
    print('Variable plots:',out)
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('-f','--config',required=True)
    a=p.parse_args();run(yaml.safe_load(expanded(a.config).read_text()))
