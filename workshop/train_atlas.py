"""ATLAS HiggsML PyTorch training. Only KaggleSet=t enters development.

AMS here is validation-tuned, using original t KaggleWeights rescaled for
the held-out fraction. It is NOT the historical private leaderboard score.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
import random
import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

METADATA = {'EventId','Weight','KaggleSet','KaggleWeight','Label','Dataset_ID'}


def expanded(path):
    return Path(os.path.expandvars(os.path.expanduser(str(path))))


def ams(signal, background, regularization=10.):
    s,b = np.asarray(signal), np.asarray(background)+regularization
    return np.sqrt(np.maximum(0., 2*((s+b)*np.log1p(s/b)-s)))


def select_threshold(y, scores, weights, regularization):
    order = np.argsort(-scores, kind='stable')
    scores,y,weights = scores[order],y[order],weights[order]
    signal = np.cumsum(weights*(y==1))
    background = np.cumsum(weights*(y==0))
    # Evaluate at the end of each tie: selection is always score >= threshold.
    ends = np.r_[np.flatnonzero(scores[:-1]!=scores[1:]),len(scores)-1]
    values = ams(signal[ends],background[ends],regularization)
    best = ends[np.argmax(values)]
    return float(scores[best]),float(ams(signal[best],background[best],regularization))


def prepare(config):
    path = expanded(config['data']['input'])
    frame = pd.read_csv(path)
    required = {'EventId','Label','KaggleSet','KaggleWeight','Weight'}
    if not required <= set(frame): raise ValueError('Missing challenge metadata columns')
    if not frame.EventId.is_unique: raise ValueError('Duplicate event IDs')
    features = config['data']['features']
    if features == 'all_physics':
        features = [c for c in frame if c.startswith(('PRI_','DER_'))]
    if not isinstance(features,list) or not features or len(set(features))!=len(features):
        raise ValueError('features must be all_physics or a unique feature list')
    if METADATA.intersection(features) or not set(features)<=set(frame):
        raise ValueError('Invalid features: never include labels, weights, IDs or partition')
    # Other partitions are never used for preprocessing, training or threshold choice.
    develop = frame.loc[frame.KaggleSet=='t'].copy().reset_index(drop=True)
    if not set(develop.Label.unique())=={'s','b'}: raise ValueError('Expected both classes')
    labels = (develop.Label=='s').to_numpy(dtype=np.int64)
    weights = develop.KaggleWeight.to_numpy(dtype=float)
    if not np.isfinite(weights).all() or (weights<0).any(): raise ValueError('Invalid weights')
    train,val = train_test_split(np.arange(len(develop)),test_size=config['split']['validation_fraction'],
        stratify=labels,random_state=config['split']['seed'])
    values = develop[features].replace(config['data']['missing_value'],np.nan)
    if values.iloc[train].isna().all().any(): raise ValueError('Feature entirely missing in training')
    preprocess = make_pipeline(SimpleImputer(strategy='median'),StandardScaler())
    xtrain = preprocess.fit_transform(values.iloc[train]).astype('float32')
    xval = preprocess.transform(values.iloc[val]).astype('float32')
    if not np.isfinite(xtrain).all() or not np.isfinite(xval).all(): raise ValueError('Nonfinite inputs')
    # Restore expected yields of the original t sample, separately per class.
    val_weights = weights[val].copy()
    for label in (0,1):
        val_weights[labels[val]==label] *= (labels==label).sum()/(labels[val]==label).sum()
    return develop,features,preprocess,train,val,xtrain,xval,labels,val_weights


def run(config):
    import torch
    from torch import nn
    from torch.utils.data import DataLoader,TensorDataset
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out = expanded(config['output']['directory'])
    if out.exists(): raise FileExistsError(f'Use a new output.directory: {out}')
    seed = int(config['split']['seed'])
    random.seed(seed);np.random.seed(seed);torch.manual_seed(seed)
    training,architecture = config['training'],config['model']
    torch.set_num_threads(int(training.get('cpu_threads',4)))
    device = torch.device(training['device'])
    if device.type=='cuda' and not torch.cuda.is_available():
        raise RuntimeError('GPU requested but unavailable; submit with run_atlas_gpu.slurm')
    if device.type=='cuda':
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.benchmark=False
    if training['weighting']!='unweighted': raise ValueError('Initial benchmark uses unweighted BCE')
    if not 0<=architecture['dropout']<1: raise ValueError('Invalid dropout')
    if not architecture['hidden_dims'] or any(int(n)<1 for n in architecture['hidden_dims']):
        raise ValueError('Invalid hidden_dims')
    if int(training['epochs'])<1 or int(training['batch_size'])<1: raise ValueError('Invalid training size')
    develop,features,preprocess,train,val,xtrain,xval,labels,val_weights = prepare(config)
    layers=[];inputs=len(features)
    for width in architecture['hidden_dims']:
        layers += [nn.Linear(inputs,int(width)),nn.ReLU(),nn.Dropout(architecture['dropout'])]
        inputs=int(width)
    layers.append(nn.Linear(inputs,1))
    model=nn.Sequential(*layers).to(device)
    optimizer=torch.optim.AdamW(model.parameters(),lr=training['learning_rate'],weight_decay=training['weight_decay'])
    criterion=nn.BCEWithLogitsLoss()
    generator=torch.Generator().manual_seed(seed)
    loader=DataLoader(TensorDataset(torch.from_numpy(xtrain),torch.from_numpy(labels[train].astype('float32'))),
        batch_size=training['batch_size'],shuffle=True,generator=generator,num_workers=0)
    xv=torch.from_numpy(xval).to(device);yv=torch.from_numpy(labels[val].astype('float32')).to(device)
    best=float('inf');best_state=None;stale=0;history=[]
    out.mkdir(parents=True)
    (out/'config.yaml').write_text(yaml.safe_dump(config,sort_keys=False))
    print('Device:',device,torch.cuda.get_device_name(0) if device.type=='cuda' else 'CPU',flush=True)
    print('Train/validation:',len(train),len(val),'features:',len(features),flush=True)
    if device.type=='cuda':
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats(device)
    start=time.perf_counter()
    for epoch in range(1,int(training['epochs'])+1):
        epoch_start=time.perf_counter()
        model.train();total=0.
        for xb,yb in loader:
            xb,yb=xb.to(device),yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss=criterion(model(xb).squeeze(1),yb)
            if not torch.isfinite(loss): raise ValueError('Nonfinite training loss')
            loss.backward();optimizer.step();total+=loss.item()*len(xb)
        model.eval()
        with torch.no_grad():
            logits=model(xv).squeeze(1)
            validation_loss=criterion(logits,yv).item()
            if not np.isfinite(validation_loss): raise ValueError('Nonfinite validation loss')
            scores=torch.sigmoid(logits).cpu().numpy()
        row={'epoch':epoch,'train_loss':total/len(train),'validation_loss':validation_loss,
             'validation_auc':roc_auc_score(labels[val],scores),
             'epoch_seconds':time.perf_counter()-epoch_start}
        history.append(row);print(json.dumps(row),flush=True)
        filled=min(24,int(24*epoch/int(training['epochs'])))
        print(f"[{'#'*filled}{'-'*(24-filled)}] Epoca {epoch}/{training['epochs']} | "
              f"train={row['train_loss']:.5f} val={validation_loss:.5f} "
              f"AUC={row['validation_auc']:.5f}",flush=True)
        if validation_loss<best:
            best=validation_loss;best_epoch=epoch;stale=0
            best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
        else: stale+=1
        if stale>=int(training['patience']): break
    model.load_state_dict(best_state);model.eval()
    with torch.no_grad(): scores=torch.sigmoid(model(xv).squeeze(1)).cpu().numpy()
    elapsed=time.perf_counter()-start
    threshold,value=select_threshold(labels[val],scores,val_weights,config['evaluation']['ams_regularization'])
    selected=scores>=threshold
    metrics={'evaluation_set':'internal_validation_from_KaggleSet_t','roc_auc_unweighted':roc_auc_score(labels[val],scores),
        'ams_validation_tuned':value,'threshold':threshold,'best_epoch':best_epoch,'epochs_run':len(history),
        'fit_seconds':elapsed,
        'parameters':sum(p.numel() for p in model.parameters()),
        'batches_per_epoch':len(loader),
        'mean_epoch_seconds':float(np.mean([r['epoch_seconds'] for r in history])),
        'gpu_peak_allocated_mb':torch.cuda.max_memory_allocated(device)/1024**2 if device.type=='cuda' else None,
        'train_events':len(train),'validation_events':len(val),'features':features,
        'signal_efficiency':float(selected[labels[val]==1].mean()),
        'background_acceptance':float(selected[labels[val]==0].mean()),
        'ams_weighting':'KaggleWeight from t, rescaled by class to full t yields; not private leaderboard',
        'device':str(device),'gpu':torch.cuda.get_device_name(0) if device.type=='cuda' else None,
        'torch':torch.__version__,'hip':torch.version.hip,'seed':seed,
        'dataset_sha256':hashlib.sha256(expanded(config['data']['input']).read_bytes()).hexdigest()}
    torch.save({'state_dict':best_state,'features':features,'model_config':architecture,'threshold':threshold},out/'best_model.pt')
    joblib.dump(preprocess,out/'preprocessing.joblib')
    pd.DataFrame(history).to_csv(out/'history.csv',index=False)
    pd.DataFrame({'EventId':develop.EventId.iloc[val].to_numpy(),'label':labels[val],'score':scores,
                  'ams_weight':val_weights}).to_csv(out/'validation_scores.csv',index=False)
    splits=np.full(len(develop),'train',dtype=object);splits[val]='validation'
    pd.DataFrame({'EventId':develop.EventId,'split':splits}).to_csv(out/'splits.csv',index=False)
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2))
    fig,axes=plt.subplots(1,3,figsize=(15,4))
    h=pd.DataFrame(history)
    axes[0].plot(h.epoch,h.train_loss,label='Train');axes[0].plot(h.epoch,h.validation_loss,label='Validation')
    axes[0].set(xlabel='Epoch',ylabel='BCE loss');axes[0].legend()
    fpr,tpr,_=roc_curve(labels[val],scores)
    axes[1].plot(fpr,tpr,label=f'AUC {metrics["roc_auc_unweighted"]:.4f}')
    axes[1].plot([0,1],[0,1],'--',color='gray');axes[1].set(xlabel='Background acceptance',ylabel='Signal efficiency');axes[1].legend()
    for label,name in [(0,'Background'),(1,'Higgs')]:
        axes[2].hist(scores[labels[val]==label],bins=np.linspace(0,1,41),density=True,histtype='step',label=name)
    axes[2].set(xlabel='Classifier score',ylabel='Unit-area density');axes[2].legend()
    fig.suptitle('ATLAS Higgs Challenge: internal validation (private set untouched)');fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(out/f'training_summary.{ext}',dpi=180)
    plt.close(fig)
    print(json.dumps(metrics,indent=2),flush=True)
    return metrics


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-f','--config',required=True)
    args=parser.parse_args()
    run(yaml.safe_load(expanded(args.config).read_text()))
