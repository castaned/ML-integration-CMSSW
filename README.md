# The official documentation can be found in [ML-integration-CMSSW documentation](https://castaned.github.io/ML-integration-CMSSW)

For the Yuca Open Data exercise, follow the [student course (in Spanish)](https://castaned.github.io/ML-integration-CMSSW/yuca-course/). It covers setup, NanoAOD processing, ROOT-to-HDF5 conversion, MLP training, and Standard Model autoencoder anomaly detection.
# Example of usage — Open Data mode

This documents the **`open_data`** variant of the framework described in *General architecture* and *Complete workflow*.

## When to use this mode

Use `open_data` instead of the default `cms_das` mode when:

- The NanoAOD `.root` files were obtained through the CERN Open Data portal (or copied by any other means) and already sit on a filesystem the cluster can see.
- There is no need to query DAS or stream files via XRootD from `eos`.
- The target cluster uses **Slurm** rather than HTCondor, and there is no CMSSW/`cmsenv` available.

## Assumptions

- The `.root` NanoAOD files for each physics process are already on the cluster, one directory per process (*e.g.* `signal/`, `background/`).
- A conda environment with ROOT, `uproot`, `awkward`, and PyTables/`h5py` is available (the examples use the name `cd`).
- You have access to `sbatch` (Slurm) or `condor_submit` (HTCondor) on the target cluster.

## 1. Data processing (filtering)

Move into `data_processing/`:

```bash
cd data_processing
```

Configure `data_processing_config.yaml`. The key difference from the standard workflow is `input_mode: "open_data"`, and the proxy block being disabled:

```yaml
proxy:
  generate: 0   # not needed in open_data mode
  voms: "cms"
  proxy_time: "192:00"
  proxy_path: "$HOME/.globus/x509up_u$(id -u)"
data_processing:
  input_mode: "open_data"
  conda_env: "cd"
  # "condor" (HTCondor) or "slurm" (array job)
  scheduler: "slurm"
  slurm_params:
    executable_file: "run_filter.sh"
    account: "p002"  # Yuca: codigo de la cuenta/proyecto asignado
    cpus: 1
    gpus: 0
    mem: "4000M"
    time: "04:00:00"
    partition: "cpu"
  processing_script: "example_files/main_process/filterNanoAOD.py"
  eos_output_dir: "/lustre/home/hacosta/Open-Data/Processed/root"
  redirector: ""
  datasets:
    - name: "background"
      ID: 0
      path: "/lustre/home/hacosta/Open-Data/Data/background"
    - name: "signal"
      ID: 1
      path: "/lustre/home/hacosta/Open-Data/Data/signal"
```

Each dataset entry replaces the `FLN`/`amount` pair used in `cms_das` mode with:

- **`path`** — a local directory; every `*.root` file inside it is used (non-recursive), **or**
- **`files`** — an explicit list of `.root` paths.

As in the standard workflow, `processing_script` (here `filterNanoAOD.py`) must:

- Accept exactly three positional arguments, in order: **input file path**, **dataset name**, **output directory**.
- Rely on `mapping.json` (generated automatically by the framework) rather than a hardcoded label, since dataset IDs are assigned from the YAML file.

Submit the jobs — one Slurm array task (or one HTCondor job) per input `.root` file:

```bash
python3 execute_data_processing.py -f data_processing_config.yaml
```

En Yuca, Slurm exige una cuenta de proyecto. El ejemplo usa `p002`; cambiala
si tu usuario tiene otra cuenta asignada. El framework incluira `#SBATCH --account=...`
en el script generado. El mismo campo `slurm_params.account` se puede usar
en la configuracion de conversion ROOT a HDF5.

## Optional QA scripts

`scripts/` ships two standalone utilities used to validate that `mini_nanotools` output matches a CMSSW-based reference skim (useful if you ever port an existing CMSSW analysis module to `open_data` mode):

- **`scripts/compresion.py`** — compares two `.root` files branch-by-branch, reporting compressed/uncompressed size per branch and flagging any "orphan" bytes on disk that don't belong to the `Events` tree (leftover CMSSW provenance trees are a common cause of unexpectedly large filtered files). Run directly with Python:

  ```bash
  python3 compresion.py file_A.root file_B.root ["Label A"] ["Label B"]
  ```

- **`scripts/test_comparacion.py`** — compares, branch-by-branch, all matching files (by relative path) between two output folders, and reports any numerical differences per branch:

  ```bash
  python3 test_comparacion.py folder_A folder_B
  ```

Both are also wired to sample Slurm submission files (`scripts/compresion.slurm`, `scripts/job.slurm`) if you need to run them on the cluster rather than on a login node — edit the hardcoded paths at the bottom of each `.slurm` file before submitting with `sbatch`.

## Evaluate QCD without retraining on it

After copying ROOT files into `$HOME/Open-Data/Data/QCD`, generate three separate
configs from the personal EWK/Wprime configs already in `$HOME/Open-Data`:

```bash
python scripts/setup_qcd_evaluation.py --account p002
```

This creates `qcd_data_processing_config.yaml`, `qcd_root2h5_config.yaml`,
and `autoencoder_qcd_model_config.yaml`. It refuses to overwrite existing
configs. The QCD sample receives `Dataset_ID=3`; the existing EWK and Wprime
HDF5 files are reused. Process QCD, convert it, and then run the new
autoencoder config. The new results go to `results_autoencoder_qcd`, leaving
the original run untouched. QCD is evaluated externally and never changes
the EWK training split, normalization, or anomaly threshold.

`execute_data_processing.py` rewrites `data_processing/mapping.json` for the
datasets in each submission. Submit the QCD-only job only after the previous
EWK/Wprime processing jobs have finished. If the original mapping is needed
later, retain a copy before submission and restore/merge it after QCD finishes.

To compare against an autoencoder trained on both known SM samples, after
converting QCD to HDF5 run `python scripts/setup_sm_mixture.py`. The generated
`$HOME/Open-Data/autoencoder_sm_mixture_model_config.yaml` keeps Wprime only
for evaluation, splits EWK and QCD separately, balances their training
sampling and validation, and writes results to a new directory. The 99th
percentile threshold refers to an equal EWK/QCD mixture, not a physical
cross-section-weighted SM prediction.

## Reprocess with the three-lepton Z+W filter

`filterNanoAOD.py` now returns `True` only when an event has at least three
selected leptons, an opposite-sign same-flavour Z candidate, and a W-lepton
candidate. The output still carries `A_pass` through `D_pass` for later
channel-specific studies. Each processing log prints the input/3-lepton/Z/W
cutflow and the channel counts. `Z_pass` is *not* a Z-mass-window cut, and
`W_pass` is *not* a W-mass-window cut; they indicate that the corresponding
candidate-finding functions succeeded.

On Yuca, generate separate configs with `python scripts/setup_wz_skim.py`.
The new ROOT, HDF5, and autoencoder outputs use `root_wz`, `h5_wz`, and
`results_autoencoder_sm_mixture_wz` respectively, so the previous unfiltered
pilot results are not overwritten. Run processing and inspect the cutflow
before conversion or training: QCD may have too few surviving events to
support the existing train/validation/test split.
