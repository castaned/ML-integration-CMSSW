#!/bin/bash

echo "Starting job on $(date)"
echo "Running on: $(hostname)"

echo "Copying files from EOS to HTCondor pool."
xrdcp -r root://eosuser.cern.ch//"$EOS_INPUT_DIR" .

echo "Running script"
apptainer run --bind $PWD:/workspace ml_container.sif execute_ml_training.py -f ml_model_config.yaml

xrdfs "$REDIRECTOR" mkdir -p "$EOS_OUTPUT_DIR"
xrdcp -r "$RESULTS_DIR" "${REDIRECTOR}/${EOS_OUTPUT_DIR}/"

echo "Time $(date)"
