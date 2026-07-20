#!/bin/bash

set -euo pipefail

echo "Starting job on $(date)"
echo "Running on: $(hostname)"

INPUT_FILE=$1
LFN=$2
OUTPUT_DIR=$3
set +u
source "${CONDA_SETUP_SCRIPT:-$HOME/miniconda3/etc/profile.d/conda.sh}"
conda activate "${CONDA_ENV_NAME:?CONDA_ENV_NAME no esta definido}"
set -u
export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH:-}"
cd "$PROJECT_DIR"

echo "Data Processing..."
python3 "$PROCESSING_SCRIPT" "$INPUT_FILE" "$LFN" "$OUTPUT_DIR"

echo "Time $(date)"
