#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --time 02:00:00
#SBATCH --output /scratch1/projects/project_pwieder_ocr/batch_job_logs/batch_download_all_ocrd_models_job-%J.txt
#SBATCH --cpus-per-task 16
#SBATCH --mem 64G

set -e

module purge
module load singularity

hostname
/opt/slurm/etc/scripts/misc/slurm_resources

# This sif file is generated with another batch script
SIF_PATH="/scratch1/projects/project_pwieder_ocr/ocrd_all_maximum_image.sif"
OCRD_MODELS_DIR="/scratch1/projects/project_pwieder_ocr/ocrd_models"
OCRD_MODELS_DIR_IN_DOCKER="/usr/local/share"

if [ ! -f "${SIF_PATH}" ]; then
  echo "Required ocrd_all_image sif file not found at: ${SIF_PATH}"
  exit 1
fi

if [ ! -d "${OCRD_MODELS_DIR}" ]; then
  mkdir -p "${OCRD_MODELS_DIR}"
fi

# Download all available ocrd models
singularity exec --bind "${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}" "${SIF_PATH}" ocrd resmgr download '*'
# Download models for ocrd-tesserocr-recognize which are not downloaded with the '*' glob
singularity exec --bind "${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}" "${SIF_PATH}" ocrd resmgr download ocrd-tesserocr-recognize '*'
# Download models for ocrd-kraken-recognize which are not downloaded with the '*' glob
singularity exec --bind "${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}" "${SIF_PATH}" ocrd resmgr download ocrd-kraken-recognize '*'
# Download models for ocrd-calamari-recognize which are not downloaded with the '*' glob
singularity exec --bind "${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}" "${SIF_PATH}" ocrd resmgr download ocrd-calamari-recognize '*'
