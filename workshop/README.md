# Practical Machine Learning in HEP

Wednesday: 3 hours. Thursday: 1 hour. Spanish student labs and instructor guide:
https://castaned.github.io/ML-integration-CMSSW/practical-ml-hep/

1. CMS original NanoAOD Higgs125→ZZ→4L vs ZZ→4L: selection, pairing, observables, then logistic/boosted/MLP classification. ATLAS CSV is optional.
2. CMS SM multilepton autoencoder and evaluation-only Wprime reference, reusing verified HDF5.

`download_higgs.py`: instructor downloads verified CSV once.
`train_higgs.py`: YAML-driven models, leakage-safe 60/20/20 split; validation by default, `--final` for test.
`setup_autoencoder.py`: personal config referencing shared instructor inputs.
`train_autoencoder.py`: existing model with distinct results and archived config.
`run_cpu.slurm`: submit from repository root with explicit account and personal log path.

Never put data, weights, labels or event IDs into classifier features. The basic classifier is unweighted and does not estimate discovery significance. CMS comparisons using the same Wprime repeatedly are exploratory.

Tests: `python -m unittest discover -s workshop/tests -v`.
Requirements: `requirements.txt` for Higgs, plus the existing CMS ML dependencies for autoencoder. No ROOT required for these prepared-data labs.

`download_cms.py`: download small original NanoAOD from verified record manifests.
`extract_fourleptons.py`: educational selection and reconstructed observables, rejection counts and provenance.
Configs: `cms_fourleptons.yaml` (selection), `cms_higgs_classifier.yaml` (training).
This is a simplified exercise, not the official CMS Higgs selection.

The extraction command performs selection, observable plots and HDF5 export together. It writes `events.h5` (flat arrays via h5py). Higgs training reads HDF5 by default, as does the CMS autoencoder. CSV reading remains available for the optional ATLAS exercise and older results.

The processing dataset_map uses the original framework ID-to-process convention. HDF5 stores Dataset_ID; dataset_map.json and data.class_id_map/data.label_mapping define binary MLP labels using ml_training.utilities.labels. Dataset_ID is never a feature.


### Parallel NanoAOD processing

`python workshop/student.py extract` submits one Slurm array task per ROOT file from the selection YAML. A dependent `afterok` job combines the selected events, sums cutflows and produces the final plots, `events.h5` and `dataset_map.json`. Empty selected files are valid; missing or failed tasks prevent the final merge. Intermediate results and per-file logs remain in the personal extraction directory with suffix `.parts`.

For a standalone YAML test (from repository root):

```bash
python workshop/processing_jobs.py submit -f "$HOME/hep-workshop/configs/selection_higgs_zz_prueba01.yaml" --output "$HOME/hep-workshop/extraction/higgs_zz_prueba01" --account curso07 --qos qoscurso07
```

Resource settings `processing.time` and `processing.memory` are fixed in the selection YAML by the course setup. Optional institutional `slurm_qos` is passed to both submissions. Run submission on the terminal; do not wrap this submission command in another `sbatch`. The old sequential `run_cpu.slurm extract` mode remains available for diagnostics.


### Compare all MLP input observables

New extractions also create `input_variables/input_variables.png` and `.pdf` (all twelve observables), plus individual PNG/PDF files named after each feature. Histograms use common bins and unit-area normalization for each process; these compare shapes, not physical rates. All selected events are shown for descriptive inspection, without training a model or changing the held-out split.

To plot an existing extraction without reprocessing or retraining, use its archived training YAML, which fixes the exact input HDF5, dataset map and feature list:

```bash
python workshop/plot_inputs.py -f "$HOME/hep-workshop/results/higgs_zz_prueba02/config.yaml" --output "$HOME/hep-workshop/results/higgs_zz_prueba02/input_variables"
```

Use a new output directory to preserve existing plots.


## Main exercise: ATLAS Higgs Challenge on AMD GPU

See `configs/atlas_higgs_gpu.yaml`, `train_atlas.py` and `run_atlas_gpu.slurm`. The shared original CSV is read directly. Copy the YAML to your personal configs, then submit from repository root:

```bash
mkdir -p "$HOME/hep-workshop/configs" "$HOME/hep-workshop/logs"
cp -n workshop/configs/atlas_higgs_gpu.yaml "$HOME/hep-workshop/configs/atlas_baseline01.yaml"
sbatch --output="$HOME/hep-workshop/logs/atlas_%j.out" workshop/run_atlas_gpu.slurm "$HOME/hep-workshop/configs/atlas_baseline01.yaml"
```

Yuca uses `ml-hep-gpu`, ROCm 6.4.3, PyTorch 2.8.0+rocm6.4 and MI210, with account curso07/QOS qoscurso07. Default network: 128/64/32/16, dropout 0.1, 20 epochs, batch 4096, AdamW. Change model/training values and a new `output.directory` in personal YAML for each experiment. GPU jobs fail clearly if GPU is unavailable.

Only KaggleSet=t is used (200k training/50k internal validation with seed 16). Median imputation (-999) and scaling fit training only. Features exclude labels/weights/IDs/partition. Training BCE is unweighted. AMS uses KaggleWeight rescaled per class for the held-out fraction; the threshold is selected on validation. This internal validation AMS is exploratory and **not the historical private leaderboard score**. Partitions b/v remain unused for fitting and threshold selection. A separate frozen-model private evaluation is required before comparison with the historical benchmark.

Outputs: best_model.pt, preprocessing.joblib, archived YAML, metrics.json (including input checksum and GPU), history.csv, splits.csv, validation_scores.csv and training_summary.png/pdf. Existing experiment folders are protected. ATLAS is the main workshop practice; CMS NanoAOD classification and the autoencoder remain complementary examples.


### YAML-first exploration and worksheets

Before training, compare all 30 ATLAS physics inputs from the original training partition:

```bash
python workshop/plot_atlas.py -f "$HOME/hep-workshop/configs/atlas_baseline01.yaml"
```

`plots.directory`, `plots.bins` and `plots.upper_quantile` control the output folder and display. Five PNG panels and a multipage PDF are produced; missing fractions are saved in CSV. Density uses all finite/non-missing events per class, before visual upper-tail zoom (default 99.5th percentile). `upper_quantile: 1.0` shows full ranges. No private events are plotted. Existing folders are protected.

For CPU comparisons use `run_atlas_cpu.slurm` with a copied YAML setting `training.device: cpu` and a new `output.directory`; no GPU is reserved. Both CPU and GPU scripts use the same environment. Training now also records parameter count, batches per epoch, mean epoch time and PyTorch peak GPU allocated memory. Memory allocation is not a GPU utilization measurement.

The course guide `practical-ml-hep/atlas-gpu/` follows physics -> variables -> YAML -> runs -> comparison. `practical-ml-hep/atlas-experiments/` provides blank tables and discussion questions. Infrastructure and historical measured results are in an optional reference appendix. Students edit personal YAML files, preserve one folder per run and complete the tables during class.


## Student CMS multilepton reproduction

The three templates `configs/cms_processing.yaml`, `cms_root2h5.yaml` and
`cms_autoencoder.yaml` describe the existing multilepton selection, ROOT/HDF5
conversion and ten-feature SM autoencoder. Do not submit templates containing
`REPLACE_` paths. From the repository root, with `ml-open-data` active:

```bash
python workshop/setup_cms.py --inputs /lustre/cursos/curso07/datos/autoencoder --tag baseline01
```

This creates personal `cms_processing_baseline01.yaml`, `cms_root2h5_baseline01.yaml`
and `cms_autoencoder_baseline01.yaml` under `$HOME/hep-workshop/configs`, plus an
explicit input-file manifest. The shared folder uses `DYjets` (lowercase j),
`WZ`, `ZZ`, `Wprime`; process labels remain 4, 5, 6, 1. Each stage points to the
personal output of the previous stage. Existing configurations/results are protected.
Full submission, monitoring and result instructions:
https://castaned.github.io/practical-ml-hep/cms-procesamiento/

These templates keep the current selection and autoencoder implementation unchanged.
Matching the historical pilot metrics additionally requires the same input files
and configuration; check the manifest and per-process counts before comparison.
