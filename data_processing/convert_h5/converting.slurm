#!/bin/bash
#SBATCH --job-name=cms_h5_conversion
#SBATCH --array=1-14
#SBATCH --cpus-per-task=1
#SBATCH --mem=1500M
#SBATCH --time=00:20:00
#SBATCH --partition=cpu
#SBATCH --output=logs/job_%A_%a.out
#SBATCH --error=logs/job_%A_%a.err
#SBATCH --export=ALL
 
LINE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" args_conversion.dat)
read -r INPUT_FILE OUTPUT_FILE <<< "$LINE"
 
bash run_conversion.sh "$INPUT_FILE" "$OUTPUT_FILE"
