#!/bin/bash

echo "Starting job on $(date)"
echo "Running on: $(hostname)"

INPUT_FILE=$1
OUTPUT_FILE=$2

#xrdcp "root://eosuser.cern.ch/${INPUT_FILE}" .
ls

apptainer exec --bind /eos conversion_container.sif python3 - <<EOF
import utilities.root as root

input_path = "$INPUT_FILE"
output_path = "$OUTPUT_FILE"
tree = "$TREE_NAME"
branches = "$BRANCHES".split(",")
max_jagged_len = int("$MAX_JAGGED_LEN")

root.root_to_h5(input_path, tree, branches, output_path, max_len=max_jagged_len)
EOF


echo "Time $(date)"
