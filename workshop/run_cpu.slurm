#!/bin/bash
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --time=00:30:00
set -euo pipefail
# Submit from repository root. Logs go to the PERSONAL submission directory.
# sbatch --account=YOUR_ACCOUNT --output="$HOME/hep-workshop/logs/%j.out" workshop/run_cpu.slurm higgs CONFIG OUTPUT
source "${CONDA_SETUP_SCRIPT:-/apps/miniconda3/etc/profile.d/conda.sh}"
conda activate "${WORKSHOP_CONDA_ENV:-ml-open-data}"
export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export OPENBLAS_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export MKL_NUM_THREADS="$SLURM_CPUS_PER_TASK"
case "$1" in
    extract-file) python workshop/processing_jobs.py worker "$2" ;;
    merge-extraction) python workshop/processing_jobs.py merge "$2" ;;
    extract) python workshop/extract_fourleptons.py -f "$2" --output "$3" ;;
    higgs) python workshop/train_higgs.py -f "$2" --output "$3" ;;
    higgs-final) python workshop/train_higgs.py -f "$2" --output "$3" --final ;;
    autoencoder) python -u workshop/train_autoencoder.py -f "$2" ;;
    *) echo 'Expected higgs, higgs-final, or autoencoder' >&2; exit 2 ;;
esac
