#!/bin/bash

echo "Starting job on $(date)"
echo "Running on: $(hostname)"

# Set CMSSW environment for EL9
export SCRAM_ARCH=el9_amd64_gcc12
cd /afs/cern.ch/work/c/castaned/CMSSW_13_3_0/src/
eval `scramv1 runtime -sh`
echo "CMSSW environment set up."
cd DeepNTuples/MyNanoAODTools/scripts/

# Set the proxy explicitly in the environment
export X509_USER_PROXY=$HOME/.globus/x509up_u$(id -u)

# Check if the proxy exists
if [ ! -f "$X509_USER_PROXY" ]; then
    echo "Error: Proxy file not found!"
    exit 1
fi

# Get dataset name from arguments
INPUT_FILE=$1
OUTPUT_FILE=$2
DATASET_FOLDER=$3
PROCESS=$4

echo "DATASET FOLDER: ${DATASET_FOLDER}"
EOS_DIR="/eos/user/c/castaned/NanoAOD_Filtered/${DATASET_FOLDER}"
echo "EOS DIR: ${EOS_DIR}"

# Avoid "File exists" error
mkdir -p filteredNanoAOD/$DATASET_FOLDER
mkdir -p filteredNanoAOD/$DATASET_FOLDER/$PROCESS

LOCAL_OUTPUT="filteredNanoAOD/${DATASET_FOLDER}/${PROCESS}"

# Ensure EOS directory exists
xrdfs eosuser.cern.ch mkdir -p $EOS_DIR


echo "XXXXXXXXXXXXXXX"
echo "XXXXXXXXXXXXXXX"
echo "XXXXXXXXXXXXXXX"
echo "Arguments received: $INPUT_FILE $OUTPUT_FILE $DATASET_FOLDER $PROCESS"


# Run NanoAOD filtering
#echo "Processing file: $INPUT_FILE"
python3 filterNanoAOD.py $INPUT_FILE $DATASET_FOLDER $PROCESS


# Copy results to EOS
echo "Copying output files to EOS: $EOS_DIR"
xrdcp -f $LOCAL_OUTPUT/*.root root://eosuser.cern.ch//$EOS_DIR/

# Clean up local files
rm -rf $LOCAL_OUTPUT

#echo "Job finished on $(date)"
