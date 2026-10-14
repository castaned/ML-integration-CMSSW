"""Collect paired workshop results into CSV; never rank using final test or Wprime AUC."""
import argparse
import csv
import json
import copy
from pathlib import Path
import yaml


def collect(config_dirs, output):
    rows=[]
    signatures={}
    for directory in config_dirs:
        for path in sorted(Path(directory).expanduser().glob('*.yaml')):
            config=yaml.safe_load(path.read_text())
            tag=config.get('workshop')
            if not tag: continue
            root=Path(tag['results_path']).expanduser()
            task=tag['task']
            metric=root/('metrics.json' if task=='higgs' else f'metrics_{config["model"]["name"]}.json')
            row={'participant':Path(directory).expanduser().resolve().name, 'task':task,
                 'group':tag['group'],'role':tag['role'],'parameter':tag['parameter'],
                 'value':json.dumps(config['model'][tag['parameter']]),'status':'pending',
                 'primary_metric':'validation_auc' if task=='higgs' else 'sm_validation_loss',
                 'metric_value':'','delta_vs_baseline':'','interpretation':'',
                 'signal_efficiency':'','background_acceptance':'','seconds':'','iterations':''}
            comparable=copy.deepcopy(config)
            comparable.pop('workshop',None)
            comparable['model'].pop(tag['parameter'],None)
            comparable['model'].pop('name',None)
            comparable['data'].pop('output_path',None)
            key=(row['participant'],task,tag['group'])
            if key in signatures and signatures[key]!=comparable:
                raise ValueError(f'{path}: paired runs differ beyond the assigned parameter')
            signatures[key]=comparable
            if metric.exists():
                m=json.loads(metric.read_text())
                if task=='higgs' and m.get('evaluation_set')!='validation':
                    raise ValueError(f'{metric}: exclude final test from the experiment comparison')
                row.update(status='completed',
                           metric_value=m.get('roc_auc_unweighted') if task=='higgs' else m.get('best_validation_loss'),
                           signal_efficiency=m.get('signal_efficiency','') if task=='higgs' else '',
                           background_acceptance=m.get('background_acceptance','') if task=='higgs' else m.get('balanced_normal_test_fpr',''),
                           seconds=m.get('fit_seconds','') if task=='higgs' else m.get('training_seconds',''),
                           iterations=m.get('iterations_run','') if task=='higgs' else m.get('epochs_run',''))
                if row['metric_value'] is None:
                    row.update(status='missing_primary_metric',metric_value='')
            rows.append(row)
    if not rows: raise ValueError('No group YAML files found')
    baseline={(r['participant'],r['task'],r['group']):r for r in rows if r['role']=='baseline'}
    for r in rows:
        if r['role']!='variation' or r['status']!='completed':continue
        ref=baseline.get((r['participant'],r['task'],r['group']))
        if not ref or ref['status']!='completed':continue
        delta=float(r['metric_value'])-float(ref['metric_value'])
        r['delta_vs_baseline']=delta
        improvement=delta if r['task']=='higgs' else -delta
        r['interpretation']='improved_on_validation' if improvement>0 else 'degraded_on_validation' if improvement<0 else 'unchanged'
    output=Path(output).expanduser()
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    print(output)
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config-dirs',nargs='+',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args();collect(a.config_dirs,a.output)
