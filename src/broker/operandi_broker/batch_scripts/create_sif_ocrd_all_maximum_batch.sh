#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 16
#SBATCH --mem 32G
#SBATCH --time 120
#SBATCH --output ./jobs_output/create_sif_job-%J.txt

module purge
module load singularity

hostname
slurm_resources

SINGULARITY_CACHE_DIR="/scratch1/users/${USER}"
CURR_DATE=$(date +"%Y_%m_%d_%H%M")
SIF_NAME="ocrd_all_image_${CURR_DATE}.sif"
OCRD_ALL_MAXIMUM_IMAGE="docker://ocrd/all:maximum"

if [ ! -d "$SINGULARITY_CACHE_DIR" ]; then
  mkdir -p "$SINGULARITY_CACHE_DIR"
fi

cd "$SINGULARITY_CACHE_DIR" || exit
singularity pull "${SIF_NAME}" ${OCRD_ALL_MAXIMUM_IMAGE}
