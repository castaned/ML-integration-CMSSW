#!/bin/bash

echo "Starting job on $(date)"
echo "Running on: $(hostname)"

INPUT_FILE=$1
FLN=$2
DATASET_DIR=$3

xrdcp "root://eosuser.cern.ch/${EOS_OUTPUT_DIR}/CMSSW.tgz" .

tar -xf CMSSW.tgz

cd CMSSW
eval `scramv1 runtime -sh`

echo "Data Processing..."
python3 "$PROCESSING_SCRIPT" "$INPUT_FILE" "$FLN" "$DATASET_DIR"

echo "Time $(date)"
