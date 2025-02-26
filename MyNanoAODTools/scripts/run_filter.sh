#!/bin/bash
echo "Starting job on $(date)"
echo "Running on: $(hostname)"


export SCRAM_ARCH=el9_amd64_gcc12
cd /afs/cern.ch/work/c/castaned/CMSSW_13_3_0/src/
eval `scramv1 runtime -sh`
echo "CMSSW environment set up."
cd DeepNTuples/MyNanoAODTools/scripts/


# Load CMS software environment
#source /cvmfs/sft.cern.ch/lcg/views/LCG_104/x86_64-el9-gcc11-opt/setup.sh

# Define EOS output directory
EOS_DIR="/eos/user/c/castaned/NanoAOD_output/"
LOCAL_OUTPUT="filteredNanoAOD"

# Set the proxy explicitly in the environment
export X509_USER_PROXY=/afs/cern.ch/user/c/castaned/.globus/x509up_u29575

# Check if the proxy exists
if [ ! -f "$X509_USER_PROXY" ]; then
    echo "Error: Proxy file not found!"
    exit 1
fi

# Run NanoAOD filtering
echo "Processing file: $1"
python3 filterNanoAOD.py $1

# Copy results to EOS
echo "Copying output files to EOS..."
xrdfs eosuser.cern.ch mkdir -p $EOS_DIR
xrdcp -f $LOCAL_OUTPUT/*.root root://eosuser.cern.ch//$EOS_DIR/

echo "Job finished on $(date)"
