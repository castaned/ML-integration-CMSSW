#!/bin/bash

set -euo pipefail

echo "Starting job on $(date)"
echo "Running on: $(hostname)"

INPUT_FILE=$1
OUTPUT_FILE=$2
set +u
source "${CONDA_SETUP_SCRIPT:-$HOME/miniconda3/etc/profile.d/conda.sh}"
conda activate "${CONDA_ENV_NAME:?CONDA_ENV_NAME no esta definido}"
set -u
export PYTHONPATH="${PROJECT_DIR}/data_processing:${PYTHONPATH:-}"

python3 - << PYEOF
import utilities.root as root

input_path = "$INPUT_FILE"
output_path = "$OUTPUT_FILE"
tree = "$TREE_NAME"
branches = "$BRANCHES".split(",")
max_jagged_len = int("$MAX_JAGGED_LEN")

root.root_to_h5(input_path, tree, branches, output_path, max_len=max_jagged_len)
PYEOF

echo "Time $(date)"
