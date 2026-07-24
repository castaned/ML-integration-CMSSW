#!/bin/bash

#SBATCH --job-name=compresion
#SBATCH --cpus-per-task=5
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --gres=gpu:1
#SBATCH --output=logs/job_%A.out
#SBATCH --error=logs/job_%A.err
#SBATCH --export=ALL
#SBATCH --partition=gpu

python3 compresion.py /lustre/home/hacosta/Open-Data/Processed/root/fondo/62AB4A36-86C6-CF48-81A5-3AEC926D349B.root  /lustre/home/hacosta/Open-Data/Processed/CMSS/62AB4A36-86C6-CF48-81A5-3AEC926D349B.root
