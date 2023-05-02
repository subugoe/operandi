#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 8
#SBATCH --mem 16G
#SBATCH --time 240
#SBATCH --output ./jobs_output/download_all_ocrd_models_job-%J.txt

module purge
module load singularity

hostname
slurm_resources

# This sif file is generated with another batch script
SIF_PATH="/scratch1/users/${USER}/ocrd_all_image_2023_04_17_1422.sif"
SCRATCH_OCRD_MODELS_BASE="/scratch1/users/${USER}/ocrd_models"

if [ ! -f "${SIF_PATH}" ]; then
  echo "Required ocrd_all_image sif file not found at: ${SIF_PATH}"
  exit 1
fi

if [ ! -d "${SCRATCH_OCRD_MODELS_BASE}" ]; then
  mkdir -p "${SCRATCH_OCRD_MODELS_BASE}"
fi

# Download all available ocrd models
singularity exec --bind "${SCRATCH_OCRD_MODELS_BASE}:/usr/local/share" "${SIF_PATH}" ocrd resmgr download '*'
# Download models for ocrd-tesserocr-recognize which are not downloaded with the previous call
singularity exec --bind "${SCRATCH_OCRD_MODELS_BASE}:/usr/local/share" "${SIF_PATH}" ocrd resmgr download ocrd-tesserocr-recognize '*'
