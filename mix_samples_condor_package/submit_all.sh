#!/bin/bash

CHUNK_SIZE=10000
INDEX_FILE=shuffled_indices.txt
OUTPUT_DIR=/eos/user/c/castaned/NanoAOD_mixed
TXT_FILES="WprimeToWZToWlepZlep_narrow_M1000_TuneCP5_13TeV-madgraph-pythia8_RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1_NANOAODSIM.txt ZZTo4L_TuneCP5_13TeV_powheg_pythia8_RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v2_NANOAODSIM_reduced.txt"

TOTAL_LINES=$(wc -l < $INDEX_FILE)
TOTAL_CHUNKS=$(( (TOTAL_LINES + CHUNK_SIZE - 1) / CHUNK_SIZE ))


# Combine all required input files
input_files="process_chunk.py,shuffled_indices.txt,WprimeToWZToWlepZlep_narrow_M1000_TuneCP5_13TeV-madgraph-pythia8_RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1_NANOAODSIM.txt,ZZTo4L_TuneCP5_13TeV_powheg_pythia8_RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v2_NANOAODSIM_reduced.txt"

for ((i=0; i<TOTAL_CHUNKS; i++)); do
    mkdir -p condor_logs/chunk_$i
    condor_submit mixSamples.jdl \
        -append "arguments = $i $CHUNK_SIZE $OUTPUT_DIR $INDEX_FILE $TXT_FILES" \
	-append "transfer_input_files = $input_files" \
        -append "output = condor_logs/chunk_$i/job_\$(Process).out" \
        -append "error  = condor_logs/chunk_$i/job_\$(Process).err" \
        -append "log    = condor_logs/chunk_$i/job_\$(Process).log"
done
