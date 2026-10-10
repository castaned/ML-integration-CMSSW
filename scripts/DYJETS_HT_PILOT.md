# DYJets HT pilot on Yuca

Run from the repository root with `ml-open-data` active. Existing configurations
and results are preserved. This pilot replaces inclusive DYJets with an unweighted
concatenation of HT 70–100, 100–200, 200–400 and 400–600 files. It is not an
inclusive or cross-section-weighted DY prediction. SM training, preprocessing,
validation and evaluation still give equal weight to DYJets, WZ and ZZ.

Generate configurations (inherits the existing Slurm account; optionally add
`--account YOUR_ACCOUNT`):

```bash
python scripts/setup_dyjets_ht_pilot.py
export CONDA_SETUP_SCRIPT=/apps/miniconda3/etc/profile.d/conda.sh
```

Wait for earlier processing jobs to finish: processing rewrites mapping.json.
Then submit filtering, keeping a copy of the old map:

```bash
cd data_processing
cp -n mapping.json mapping_before_dyjets_ht.json
python execute_data_processing.py -f "$HOME/Open-Data/dyjets_ht_processing_config.yaml"
squeue -u "$USER"
```

Inspect job logs and selected-event cutflows. Only after filtering finishes
successfully, submit conversion:

```bash
cd convert_h5
python execute_convert_root2h5.py -f "$HOME/Open-Data/dyjets_ht_root2h5_config.yaml" --skip-empty-trees --skip-existing
squeue -u "$USER"
```

After conversion finishes successfully, return to the repository root and check
all ten features in DYJets, existing WZ/ZZ and existing Wprime HDF5 files:

```bash
cd ../..
python scripts/check_dyjets_ht_pilot.py -f "$HOME/Open-Data/autoencoder_dyjets_ht_10features_config.yaml"
```

Missing branches in reused HDF5 files require reconversion of the corresponding
existing ROOT samples; do not drop checks or use sentinel values. If DYJets still
has few selected events, report this as a statistical limitation.

Train on a Yuca compute allocation, using the same split, seed and architecture
for both runs. Each output folder must be new (do not rerun over existing results):

```bash
python ml_training/execute_ml_training.py -f "$HOME/Open-Data/autoencoder_dyjets_ht_5features_config.yaml"
python ml_training/execute_ml_training.py -f "$HOME/Open-Data/autoencoder_dyjets_ht_10features_config.yaml"
```

The five-feature baseline uses MET_pt, M3l, Z_deltaR, Z_mass and Lep_pt_sum.
The ten-feature variant adds Z_pt, Lep1Z_pt, Lep2Z_pt, Lep3W_pt and W_mt.
Channel-dependent values come only from the passing A/B/C/D channel. W_mt is
computed as sqrt(2 pT(lepton) MET [1-cos(delta_phi)]) rather than using the existing
Wmass branch, which uses a different definition. Hidden layers remain 16/8,
latent dimension 2; inputs and outputs become 10-dimensional in the expanded run.

Results live in `$HOME/Open-Data/Processed/results_autoencoder_dyjets_ht_5features`
and `results_autoencoder_dyjets_ht_10features`. Use loss, scores_by_process, ROC
and metrics files to compare them. Wprime is evaluation-only; repeated inspection
of its performance makes these comparisons exploratory, requiring a fresh final
evaluation sample before any definitive claim.
