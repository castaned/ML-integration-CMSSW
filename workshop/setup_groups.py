"""Generate four paired YAML experiments, without changing the common data or split."""
import argparse
import copy
from pathlib import Path
import yaml


def generate(reference, directory, results, task):
    base = yaml.safe_load(Path(reference).expanduser().read_text())
    directory = Path(directory).expanduser().resolve()
    results = Path(results).expanduser().resolve()
    if directory.exists() or results.exists():
        raise FileExistsError('Use new config and result directories')
    if task == 'higgs':
        base['model'].update(type='mlp', hidden_dims=[32,16], learning_rate=0.001, batch_size=128, max_iter=100)
        changes = [('hidden_dims',[64,32]), ('learning_rate',0.0003), ('batch_size',256), ('max_iter',200)]
    elif task == 'autoencoder':
        base['model'].update(hidden_dims=[16,8], learning_rate=0.001, batch_size=256, epochs=60, latent_dim=2, export_onnx=False)
        changes = [('hidden_dims',[32,16]), ('learning_rate',0.0003), ('batch_size',128), ('latent_dim',4)]
    else:
        raise ValueError('task must be higgs or autoencoder')
    directory.mkdir(parents=True)
    for group, (parameter,value) in enumerate(changes,1):
        for role in ('baseline','variation'):
            config = copy.deepcopy(base)
            name=f'{task}_group{group}_{role}'
            out=str(results/name)
            config['workshop']={'task':task,'group':group,'role':role,'parameter':parameter,
                                'baseline_value':base['model'][parameter], 'variation_value':value,
                                'results_path':out}
            if role=='variation': config['model'][parameter]=value
            if task=='autoencoder':
                config['data']['output_path']=out
                config['model']['name']=name
            target=directory/(name+'.yaml')
            target.write_text(yaml.safe_dump(config,sort_keys=False))
            print(target)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',required=True)
    p.add_argument('--config-dir',required=True)
    p.add_argument('--results-root',required=True)
    p.add_argument('--task',choices=['higgs','autoencoder'],required=True)
    a=p.parse_args();generate(a.reference,a.config_dir,a.results_root,a.task)
