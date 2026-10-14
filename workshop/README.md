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
