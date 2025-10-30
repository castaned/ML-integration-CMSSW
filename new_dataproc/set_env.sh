#!/bin/bash

echo "Starting job on $(date)"
echo "Running on: $(hostname)"

mkdir -p $EOS_OUTPUT_DIR
tar -zcf "$EOS_OUTPUT_DIR/CMSSW.tgz" $AFS_CMS_BASE

echo "Time $(date)"
