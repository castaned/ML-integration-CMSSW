#!/bin/bash
#SBATCH --job-name=cms_processing
#SBATCH --array=1-14
#SBATCH --cpus-per-task=1
#SBATCH --mem=4000M
#SBATCH --time=04:00:00
#SBATCH --partition=cpu
#SBATCH --output=logs/job_%A_%a.out
#SBATCH --error=logs/job_%A_%a.err
#SBATCH --export=ALL
 
LINE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" args_processing.dat)
IFS=',' read -r INPUT_FILE LFN OUTPUT_SUBDIR <<< "$LINE"
INPUT_FILE=$(echo "$INPUT_FILE" | xargs)
LFN=$(echo "$LFN" | xargs)
OUTPUT_SUBDIR=$(echo "$OUTPUT_SUBDIR" | xargs)
 
bash run_filter.sh "$INPUT_FILE" "$LFN" "$OUTPUT_SUBDIR"
