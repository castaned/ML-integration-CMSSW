"""Educational CMS NanoAOD -> selected four-lepton observables, NOT official HZZ selection."""
import argparse
import itertools
import json
import math
from pathlib import Path
import numpy as np
import awkward as ak
import pandas as pd
import uproot
import yaml


def vector(pt, eta, phi, mass):
    px, py, pz = pt * math.cos(phi), pt * math.sin(phi), pt * math.sinh(eta)
    return np.array([math.sqrt(px*px+py*py+pz*pz+mass*mass), px, py, pz])


def mass(v):
    return math.sqrt(max(0., v[0]**2 - np.dot(v[1:], v[1:])))


def candidate(leptons, cuts):
    # Simple reproducible exercise: exactly four selected leptons.
    if len(leptons) != 4:
        return None, 'four_selected'
    leptons = sorted(leptons, key=lambda l: -l['pt'])
    if any(l['pt'] < cut for l, cut in zip(leptons, cuts['ordered_pt'])):
        return None, 'ordered_pt'
    pairs = []
    for a, b in itertools.combinations(range(4), 2):
        la, lb = leptons[a], leptons[b]
        if la['flavor'] == lb['flavor'] and la['charge'] != lb['charge']:
            pairs.append(((a,b), mass(la['v'] + lb['v'])))
    # Both pairs must be opposite-sign same-flavor; choose Z1 closest to mZ.
    possibilities = []
    for pair, m1 in pairs:
        remaining = tuple(i for i in range(4) if i not in pair)
        for other, m2 in pairs:
            if other == remaining:
                possibilities.append((abs(m1-91.1876), pair, other, m1, m2))
    if not possibilities:
        return None, 'sfos_pairs'
    _, p1, p2, m1, m2 = min(possibilities)
    if not cuts['z1_mass'][0] <= m1 <= cuts['z1_mass'][1] or not cuts['z2_mass'][0] <= m2 <= cuts['z2_mass'][1]:
        return None, 'pair_masses'
    total = sum((l['v'] for l in leptons), np.zeros(4))
    m4 = mass(total)
    if not cuts['fourlepton_mass'][0] <= m4 <= cuts['fourlepton_mass'][1]:
        return None, 'fourlepton_mass'
    z1 = leptons[p1[0]]['v'] + leptons[p1[1]]['v']
    z2 = leptons[p2[0]]['v'] + leptons[p2[1]]['v']
    row = {'DER_m4l': m4, 'DER_mZ1': m1, 'DER_mZ2': m2,
           'DER_pt4l': float(np.hypot(total[1],total[2])),
           'DER_ptZ1': float(np.hypot(z1[1],z1[2])), 'DER_ptZ2': float(np.hypot(z2[1],z2[2])),
           'DER_sum_lepton_pt': sum(l['pt'] for l in leptons)}
    row.update({f'PRI_lepton{i+1}_pt': l['pt'] for i,l in enumerate(leptons)})
    return row, 'selected'


def extract(config, output):
    output = Path(output).expanduser()
    if output.exists(): raise FileExistsError('Use a new extraction directory')
    cuts = config['selection']
    rows, flows, provenance = [], {}, []
    files_seen = set()
    for sample in config['samples']:
        label = sample['label']
        if label not in ('s','b'): raise ValueError('label must be s or b')
        flow = {}
        for filename in sample['files']:
            path = Path(filename).expanduser().resolve()
            if path in files_seen: raise ValueError('Duplicate input file across samples')
            files_seen.add(path)
            with uproot.open(path, decompression_executor=uproot.source.futures.TrivialExecutor(),
                             interpretation_executor=uproot.source.futures.TrivialExecutor()) as source:
                tree = source['Events']
                fields = ['run','luminosityBlock','event','MET_pt']
                fields += ['Muon_'+s for s in ('pt','eta','phi','mass','charge','mediumId','pfRelIso04_all')]
                fields += ['Electron_'+s for s in ('pt','eta','phi','mass','charge','cutBased')]
                missing = set(fields)-set(tree.keys())
                if missing: raise ValueError(f'{path}: missing {sorted(missing)}')
                stop = min(tree.num_entries, int(config['max_events_per_file']))
                provenance.append({'file': str(path), 'entries': tree.num_entries, 'processed': stop,
                                   'record': sample['record'], 'label': label})
                entry = 0
                for arrays in tree.iterate(fields, entry_stop=stop, step_size=2000, library='ak'):
                    # Convert each small chunk once: avoid costly per-scalar Awkward access.
                    for event in ak.to_list(arrays):
                        flow['input'] = flow.get('input',0)+1
                        leptons = []
                        for collection, flavor, eta_max in [('Muon',13,2.4),('Electron',11,2.5)]:
                            for i in range(len(event[collection+'_pt'])):
                                pt, eta, phi, m = [float(event[collection+'_'+f][i]) for f in ('pt','eta','phi','mass')]
                                if pt < cuts['lepton_pt_min'] or abs(eta)>eta_max: continue
                                if collection == 'Muon':
                                    if not bool(event['Muon_mediumId'][i]) or float(event['Muon_pfRelIso04_all'][i])>cuts['muon_iso_max']: continue
                                elif int(event['Electron_cutBased'][i]) < cuts['electron_cutbased_min']: continue
                                leptons.append({'pt':pt,'flavor':flavor,'charge':int(event[collection+'_charge'][i]),
                                                'v':vector(pt,eta,phi,m)})
                        row, stage = candidate(leptons,cuts)
                        flow[stage] = flow.get(stage,0)+1
                        if row is not None:
                            row.update(PRI_met=float(event['MET_pt']),Label=label,
                                       EventId=f'{sample["name"]}:{path.name}:{entry}')
                            rows.append(row)
                        entry += 1
        flows[sample['name']] = flow
    if not rows: raise ValueError('No selected events; inspect selection and input statistics')
    frame = pd.DataFrame(rows)
    if not frame.EventId.is_unique: raise ValueError('Duplicate event provenance IDs')
    output.mkdir(parents=True)
    frame.to_csv(output/'events.csv',index=False)
    (output/'config.yaml').write_text(yaml.safe_dump(config,sort_keys=False))
    (output/'cutflow.json').write_text(json.dumps(flows,indent=2))
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for ax,feature,interval in zip(axes,('DER_m4l','DER_mZ1','DER_mZ2'),((70,180),(40,120),(12,120))):
        for label,name in [('s','Higgs125'),('b','ZZ4L')]:
            values=frame.loc[frame.Label==label,feature]
            if len(values): ax.hist(values,bins=np.linspace(*interval,31),density=True,histtype='step',label=name)
        ax.set(xlabel=feature+' [GeV]',ylabel='Unit-area density'); ax.legend()
    fig.tight_layout();fig.savefig(output/'observables.pdf');fig.savefig(output/'observables.png',dpi=180);plt.close(fig)
    print(json.dumps(flows,indent=2))
    print(frame.Label.value_counts().to_dict())
    return frame


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('-f','--config',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    extract(yaml.safe_load(Path(a.config).read_text()),a.output)
