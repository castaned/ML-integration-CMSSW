#!/bin/bash

# Set the directory containing the sample folders
BASE_DIR="/eos/user/c/castaned/NanoAOD_Filtered"

# Navigate to the base directory
cd "$BASE_DIR" || exit

# Loop over each sample directory
for sample in */; do
    # Remove trailing slash from directory name
    sample_name="${sample%/}"
    
    # Create a .txt file with the list of .root files containing full paths
    find "$sample_name" -type f -name "*.root" | sed "s|^|$BASE_DIR/|" > "${sample_name}.txt"
    
    echo "Created ${sample_name}.txt with list of .root files including full paths."
done

