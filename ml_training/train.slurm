#!/bin/bash

#SBATCH --job-name=cms_ml_training
#SBATCH --cpus-per-task=5
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --gres=gpu:1
#SBATCH --output=logs/job_%A.out
#SBATCH --error=logs/job_%A.err
#SBATCH --export=ALL
#SBATCH --partition=gpu
set -euo pipefail
mkdir -p logs

echo "Starting job on $(date)"
echo "Running on: $(hostname)"

EOS_INPUT_DIR="${EOS_INPUT_DIR:-}"
EOS_OUTPUT_DIR="${EOS_OUTPUT_DIR:-}"
REDIRECTOR="${REDIRECTOR:-root://eosuser.cern.ch}"
RESULTS_DIR="${RESULTS_DIR:-results/}"
CONDA_ENV_NAME="${CONDA_ENV_NAME:?CONDA_ENV_NAME no esta definido}"

if [ -n "$EOS_INPUT_DIR" ]; then
    echo "Copying files from EOS."
    xrdcp -r "${REDIRECTOR}/${EOS_INPUT_DIR}" .
fi
set +u
source "${CONDA_SETUP_SCRIPT:-$HOME/miniconda3/etc/profile.d/conda.sh}"
conda activate "$CONDA_ENV_NAME"
set -u
echo "Running training"
python3 execute_ml_training.py -f ml_model_config.yaml

if [ -n "$EOS_OUTPUT_DIR" ]; then
    xrdfs "$REDIRECTOR" mkdir -p "$EOS_OUTPUT_DIR"
    xrdcp -r "$RESULTS_DIR" "${REDIRECTOR}/${EOS_OUTPUT_DIR}/"
fi

echo "Time $(date)"
