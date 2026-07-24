#!/bin/bash

#SBATCH --job-name=comparacion_filtrado
#SBATCH --cpus-per-task=5
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --gres=gpu:1
#SBATCH --output=logs/job_%A.out
#SBATCH --error=logs/job_%A.err
#SBATCH --export=ALL
#SBATCH --partition=gpu

python3 test_comparacion.py  /lustre/home/hacosta/Open-Data/Processed/root/fondo /lustre/home/hacosta/Open-Data/Processed/CMSS 

