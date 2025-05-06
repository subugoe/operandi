#!/bin/bash
#SBATCH --partition standard96:shared
#SBATCH --time 6:00:00
#SBATCH --output download_all_ocrd_models_job-%J.txt
#SBATCH --cpus-per-task 16
#SBATCH --mem 32G

set -e

module purge
module load apptainer

hostname
# /opt/slurm/etc/scripts/misc/slurm_resources

# This sif file is generated with another batch script
SIF_PATH="/mnt/lustre-emmy-hdd/projects/project_pwieder_ocr_nhr/ocrd_processor_sifs/ocrd_all_maximum_image.sif"
OCRD_MODELS_DIR="/mnt/lustre-emmy-hdd/projects/project_pwieder_ocr_nhr/ocrd_models"
OCRD_MODELS_DIR_IN_DOCKER="/usr/local/share"

if [ ! -f "${SIF_PATH}" ]; then
  echo "Required ocrd_all_image sif file not found at: ${SIF_PATH}"
  exit 1
fi

if [ ! -d "${OCRD_MODELS_DIR}" ]; then
  mkdir -p "${OCRD_MODELS_DIR}"
fi

apptainer exec --bind "${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}" "${SIF_PATH}" ocrd resmgr download -o '*'
apptainer exec --bind "${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}" "${SIF_PATH}" ocrd resmgr download -o ocrd-tesserocr-recognize '*'
apptainer exec --bind "${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}" "${SIF_PATH}" ocrd resmgr download -o ocrd-calamari-recognize '*'
apptainer exec --bind "${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}" "${SIF_PATH}" ocrd resmgr download -o ocrd-kraken-recognize '*'
apptainer exec --bind "${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}" "${SIF_PATH}" ocrd resmgr download -o ocrd-sbb-binarize '*'
apptainer exec --bind "${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}" "${SIF_PATH}" ocrd resmgr download -o ocrd-cis-ocropy-recognize '*'