#!/bin/bash
echo "Setting up CMSSW"
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh

echo "Moving to CMSSW directory"
cd /afs/cern.ch/work/c/castaned/CMSSW_13_3_0/src/  # Adjust to your setup
cmsenv
cd -

echo "Running the NanoAOD reduction script"
python3 reduce_nanoaod.py "$1" "$2"

