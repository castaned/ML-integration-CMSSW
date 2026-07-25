# The official documentation can be found in [ML-integration-CMSSW documentation](https://castaned.github.io/ML-integration-CMSSW)
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
