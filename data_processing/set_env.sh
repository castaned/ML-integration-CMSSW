#!/bin/bash

echo "Starting job on $(date)"
echo "Running on: $(hostname)"

mkdir -p "$EOS_OUTPUT_DIR"
tar -zcf "$EOS_OUTPUT_DIR/CMSSW.tgz" --transform="s|$(basename "$AFS_CMS_BASE")|CMSSW|" -C "$(dirname "$AFS_CMS_BASE")" "$(basename "$AFS_CMS_BASE")"

echo "Time $(date)"
