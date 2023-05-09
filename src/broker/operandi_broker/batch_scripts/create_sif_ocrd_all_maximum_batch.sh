#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 16
#SBATCH --mem 32G
#SBATCH --time 240
#SBATCH --output ./jobs_output/create_sif_job-%J.txt

module purge
module load singularity

hostname
slurm_resources

SINGULARITY_CACHE_DIR="/scratch1/users/${USER}"
SIF_NAME="ocrd_all_maximum_image.sif"
OCRD_ALL_MAXIMUM_IMAGE="docker://ocrd/all:maximum"

if [ ! -d "${SINGULARITY_CACHE_DIR}" ]; then
  mkdir -p "${SINGULARITY_CACHE_DIR}"
fi

cd "${SINGULARITY_CACHE_DIR}" || exit
singularity pull "${SIF_NAME}" "${OCRD_ALL_MAXIMUM_IMAGE}"
