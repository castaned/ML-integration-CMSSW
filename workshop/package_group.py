"""Package only representative figures, numbers and paired YAMLs for manual course upload."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
import zipfile
import yaml
from collect_results import collect


def package(config_dir, group, output):
    config_dir=Path(config_dir).expanduser()
    output=Path(output).expanduser()
    if output.exists():raise FileExistsError(output)
    configs={}
    for path in config_dir.glob('*.yaml'):
        c=yaml.safe_load(path.read_text())
        tag=c.get('workshop',{})
        if tag.get('group')==group:
            if tag['role'] in configs:raise ValueError('One task and one pair per delivery')
            configs[tag['role']]=(path,c)
    if set(configs)!={'baseline','variation'}:raise ValueError('Both group YAMLs are required')
    tasks={c['workshop']['task'] for _,c in configs.values()}
    if len(tasks)!=1:raise ValueError('Do not mix tasks in one delivery')
    task=tasks.pop()
    with tempfile.TemporaryDirectory() as temp:
        temp=Path(temp)
        rows=collect([config_dir],temp/'comparacion.csv',group)
        if len(rows)!=2 or any(r['status']!='completed' for r in rows):
            raise ValueError('Finish both paired trainings before submitting')
        scores={}
        for role,(source,c) in configs.items():
            dest=temp/role;dest.mkdir()
            shutil.copy2(source,dest/'config.yaml')
            root=Path(c['workshop']['results_path']).expanduser()
            if task=='higgs':
                metrics=root/'metrics.json'
                figures=[root/'classification.png']
                import pandas as pd
                scores[role]=pd.read_csv(root/'scores.csv')
            else:
                name=c['model']['name']
                metrics=root/f'metrics_{name}.json'
                figures=[root/f'loss_{name}.pdf',root/f'scores_by_process_{name}.pdf']
            shutil.copy2(metrics,dest/'metrics.json')
            if (root/'dataset_map.json').exists():
                shutil.copy2(root/'dataset_map.json',dest/'dataset_map.json')
            for figure in figures:
                if not figure.exists():raise FileNotFoundError(figure)
                shutil.copy2(figure,dest/figure.name)
        if task=='higgs':
            if set(scores['baseline'].EventId)!=set(scores['variation'].EventId):
                raise ValueError('ROC comparison requires identical validation events')
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from sklearn.metrics import roc_curve,roc_auc_score
            fig,ax=plt.subplots(figsize=(6,5))
            for role,frame in scores.items():
                fpr,tpr,_=roc_curve(frame.label,frame.score)
                ax.plot(fpr,tpr,label=f'{role}: AUC {roc_auc_score(frame.label,frame.score):.3f}')
            ax.plot([0,1],[0,1],'--',color='gray')
            ax.set(xlim=(0,1),ylim=(0,1),xlabel='Background acceptance',ylabel='Higgs efficiency',title='Validation ROC: same events')
            ax.legend();fig.tight_layout();fig.savefig(temp/'ROC_comparison.png',dpi=180);plt.close(fig)
        (temp/'conclusiones.md').write_text('# Conclusiones del grupo\n\n'
            '1. Hipótesis antes de entrenar:\n\n2. Parámetro cambiado y valores:\n\n'
            '3. Observación frente a la referencia y coste:\n\n4. Limitación y siguiente prueba:\n',encoding='utf-8')
        output.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(temp.rglob('*')):
                if path.is_file():archive.write(path,path.relative_to(temp).as_posix())
        with zipfile.ZipFile(output) as archive:
            if archive.testzip():raise ValueError('Invalid delivery archive')
    print(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config-dir',required=True)
    p.add_argument('--group',type=int,choices=range(1,5),required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args();package(a.config_dir,a.group,a.output)
