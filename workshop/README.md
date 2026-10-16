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
