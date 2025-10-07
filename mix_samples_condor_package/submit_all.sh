#!/bin/bash

# Parameters
CHUNK_SIZE=50000
INDEX_FILE=shuffled_indices.txt
OUTPUT_DIR=/eos/user/c/castaned/NanoAOD_mixed

# Space-separated list of .txt files (easy to read and pass as arguments)
TXT_FILES="WZ.txt,TT.txt,WprimeToWZToWlepZlep_narrow_M1000_TuneCP5_13TeV-madgraph-pythia8_RunIISummer20UL18NanoAODv9-106X_upgrade2018_realistic_v16_L1v1-v1_NANOAODSIM.txt"

# Count total lines and compute number of chunks
TOTAL_LINES=$(wc -l < "$INDEX_FILE")
TOTAL_CHUNKS=$(( (TOTAL_LINES + CHUNK_SIZE - 1) / CHUNK_SIZE ))

# Common input files
input_files="run_process_chunk.sh,process_chunk.py,$INDEX_FILE,$TXT_FILES"

echo "Total lines in index file: $TOTAL_LINES"
echo "Submitting $TOTAL_CHUNKS chunks with chunk size $CHUNK_SIZE"

mkdir -p condor_logs

for ((i=0; i<TOTAL_CHUNKS; i++)); do
    chunk_log_dir="condor_logs/chunk_$i"
    mkdir -p "$chunk_log_dir"

    job_jdl="chunk_$i.jdl"
    cat > "$job_jdl" <<EOF
Universe       = vanilla
Executable     = run_process_chunk.sh
ShouldTransferFiles = YES
WhenToTransferOutput = ON_EXIT
transfer_input_files = $input_files

request_cpus = 1
request_memory = 1500M
request_disk = 1GB
+JobFlavour = "workday"

Arguments = $i $CHUNK_SIZE $OUTPUT_DIR $INDEX_FILE $TXT_FILES
Output    = $chunk_log_dir/job_\$(Process).out
Error     = $chunk_log_dir/job_\$(Process).err
Log       = $chunk_log_dir/job_\$(Process).log

Queue
EOF

    condor_submit "$job_jdl"
done


