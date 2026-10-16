#!/bin/bash
#SBATCH --partition=gpu
#SBATCH --gres=gpu:MI210:1
#SBATCH --account=curso07
#SBATCH --qos=qoscurso07
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --job-name=atlas_higgs
set -euo pipefail
module load rocm/6.4.3
source /apps/miniconda3/etc/profile.d/conda.sh
conda activate ml-hep-gpu
export MPLBACKEND=Agg
python -u workshop/train_atlas.py -f "$1"
