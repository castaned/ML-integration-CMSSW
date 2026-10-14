"""Student interface: fixed course setup, YAML-only model changes, personal Slurm outputs."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime
import yaml
from setup_groups import generate
from setup_autoencoder import generate as prepare_ae

REPO=Path(__file__).resolve().parents[1]
WORKSPACE=Path.home()/'hep-workshop'


def prepare(settings_path,group,workspace=WORKSPACE):
    workspace=Path(workspace).resolve()
    state_path=workspace/'course_state.json'
    if state_path.exists():raise FileExistsError('Personal course setup already exists')
    settings=yaml.safe_load(Path(settings_path).expanduser().read_text())
    root=Path(settings['nanoaod_root']).expanduser().resolve()
    account=str(settings['slurm_account'])
    if not account.strip():raise ValueError('Missing institutional Slurm account')
    selection=yaml.safe_load((REPO/'workshop/configs/cms_fourleptons.yaml').read_text())
    for sample in selection['samples']:
        files=sorted((root/sample['name']).glob('*.root'))
        if not files:raise FileNotFoundError(root/sample['name'])
        sample['files']=[str(p) for p in files]
    configs=workspace/'configs';configs.mkdir(parents=True,exist_ok=True)
    (workspace/'logs').mkdir(exist_ok=True)
    selection_path=configs/'selection.yaml'
    if selection_path.exists():raise FileExistsError(selection_path)
    selection_path.write_text(yaml.safe_dump(selection,sort_keys=False))
    classifier=yaml.safe_load((REPO/'workshop/configs/cms_higgs_classifier.yaml').read_text())
    classifier['data']['input']=str(workspace/'extraction/baseline/events.h5')
    classifier['data']['label_mapping']=str(workspace/'extraction/baseline/dataset_map.json')
    classifier_path=configs/'classifier.yaml'
    if classifier_path.exists():raise FileExistsError(classifier_path)
    classifier_path.write_text(yaml.safe_dump(classifier,sort_keys=False))
    ae_path=configs/'ae_baseline.yaml'
    prepare_ae(settings['autoencoder_reference'],ae_path,workspace/'results/ae_reference')
    state={'group':group,'account':account,'conda_env':settings.get('conda_env','ml-open-data'),
           'selection':str(selection_path),'selection_reference':selection,
           'extraction':str(workspace/'extraction/baseline'),'configs':{},'expected':{}}
    for task,reference in [('higgs',classifier_path),('autoencoder',ae_path)]:
        folder=configs/f'groups_{task}_{workspace.parent.name}'
        generate(reference,folder,workspace/'results'/f'groups_{task}',task,selected_group=group)
        state['configs'][task]={}
        for role in ('baseline','variation'):
            path=folder/f'{task}_group{group}_{role}.yaml'
            state['configs'][task][role]=str(path)
            personal=yaml.safe_load(path.read_text())
            if role=='variation':
                parameter=personal['workshop']['parameter']
                personal['model'][parameter]=personal['workshop']['baseline_value']
                path.write_text(yaml.safe_dump(personal,sort_keys=False))
            state['expected'][str(path)]=personal
    state_path.write_text(json.dumps(state,indent=2))
    for task,roles in state['configs'].items():
        print(task,'Edit model parameter only:',roles['variation'])
    return state


def validate(config,expected,role):
    candidate=copy.deepcopy(config);reference=copy.deepcopy(expected)
    if role=='variation':
        parameter=expected['workshop']['parameter']
        if candidate['model'].get(parameter)==reference['model'].get(parameter):
            raise ValueError('Edit your assigned model parameter in the variation YAML before submitting')
        candidate['model'].pop(parameter,None);reference['model'].pop(parameter,None)
    if candidate!=reference:
        raise ValueError('Only the assigned model parameter in the variation YAML may change')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    setup=sub.add_parser('prepare');setup.add_argument('--settings',required=True)
    setup.add_argument('--group',type=int,choices=range(1,5),required=True)
    sub.add_parser('inspect');sub.add_parser('extract')
    train=sub.add_parser('train');train.add_argument('--task',choices=['higgs','autoencoder'],required=True)
    train.add_argument('--role',choices=['baseline','variation'],required=True)
    sub.add_parser('files')
    sub.add_parser('collect')
    sub.add_parser('final')
    package_parser=sub.add_parser('package');package_parser.add_argument('--task',choices=['higgs','autoencoder'],required=True)
    args=p.parse_args()
    if args.command=='prepare':prepare(args.settings,args.group);return
    state=json.loads((WORKSPACE/'course_state.json').read_text())
    if args.command in ('collect','package'):
        stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
        if args.command=='collect':
            from collect_results import collect
            folders=[Path(roles['baseline']).parent for roles in state['configs'].values()]
            collect(folders,WORKSPACE/f'comparacion_grupo{state["group"]}_{stamp}.csv',state['group'])
        else:
            from package_group import package
            folder=Path(state['configs'][args.task]['baseline']).parent
            package(folder,state['group'],WORKSPACE/f'entrega_grupo{state["group"]}_{args.task}_{stamp}.zip')
        return
    if args.command=='files':
        for task,roles in state['configs'].items():
            for role,path in roles.items():
                print(task,role,'YAML:',path)
                print('Results:',state['expected'][path]['workshop']['results_path'])
        return
    selection=yaml.safe_load(Path(state['selection']).read_text())
    if selection!=state['selection_reference']:raise ValueError('Keep the common selection unchanged')
    if args.command=='inspect':
        import uproot
        for sample in selection['samples']:
            with uproot.open(sample['files'][0]) as source:
                tree=source['Events'];print(sample['name'],'events:',tree.num_entries)
                print(tree.arrays(['nMuon','nElectron','MET_pt'],entry_stop=3))
        return
    if args.command=='extract':
        mode='extract';config=state['selection'];output=state['extraction']
    else:
        task='higgs' if args.command=='final' else args.task
        role='variation' if args.command=='final' else args.role
        config=state['configs'][task][role]
        c=yaml.safe_load(Path(config).read_text());validate(c,state['expected'][config],role)
        mode=task;output=c['workshop']['results_path']
        if args.command=='final':
            recorded=Path(output)/'config.yaml'
            if not recorded.exists() or yaml.safe_load(recorded.read_text())!=c:
                raise ValueError('Final test requires the frozen variation already evaluated on validation')
            mode='higgs-final';output=output+'_final'
    if Path(output).exists():raise FileExistsError('This experiment already has results; keep them for comparison')
    env=os.environ.copy();env['WORKSHOP_CONDA_ENV']=state['conda_env']
    command=['sbatch',f'--account={state["account"]}',f'--output={WORKSPACE}/logs/%j.out',
             str(REPO/'workshop/run_cpu.slurm'),mode,config]
    if mode!='autoencoder':command.append(output)
    subprocess.run(command,cwd=REPO,env=env,check=True)


if __name__=='__main__':main()
