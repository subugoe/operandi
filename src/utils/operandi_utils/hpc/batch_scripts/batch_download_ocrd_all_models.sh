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

SIFS_DIR_PATH="/mnt/lustre-emmy-hdd/projects/project_pwieder_ocr_nhr/ocrd_processor_sifs"

if [ ! -d "${SIFS_DIR_PATH}" ]; then
  echo "Required sifs directory not found at: ${SIFS_DIR_PATH}"
  exit 1
fi

OCRD_MODELS_DIR="/mnt/lustre-emmy-hdd/projects/project_pwieder_ocr_nhr/ocrd_models"
if [ ! -d "${OCRD_MODELS_DIR}" ]; then
  mkdir -p "${OCRD_MODELS_DIR}"
fi

# These sif images are previously generated with another batch script in the same directory.
apptainer exec --bind "${OCRD_MODELS_DIR}:/usr/local/share" "${SIFS_DIR_PATH}/ocrd_tesserocr.sif" ocrd resmgr download -o ocrd-tesserocr-recognize '*'
apptainer exec --bind "${OCRD_MODELS_DIR}:/usr/local/share" "${SIFS_DIR_PATH}/ocrd_calamari.sif" ocrd resmgr download -o ocrd-calamari-recognize '*'
apptainer exec --bind "${OCRD_MODELS_DIR}:/usr/local/share" "${SIFS_DIR_PATH}/ocrd_kraken.sif" ocrd resmgr download -o ocrd-kraken-recognize '*'
apptainer exec --bind "${OCRD_MODELS_DIR}:/usr/local/share" "${SIFS_DIR_PATH}/ocrd_sbb_binarization.sif" ocrd resmgr download -o ocrd-sbb-binarize '*'
apptainer exec --bind "${OCRD_MODELS_DIR}:/usr/local/share" "${SIFS_DIR_PATH}/ocrd_cis.sif" ocrd resmgr download -o ocrd-cis-ocropy-recognize '*'
apptainer exec --bind "${OCRD_MODELS_DIR}:/usr/local/share" "${SIFS_DIR_PATH}/ocrd_eynollah.sif" ocrd resmgr download -o ocrd-eynollah-segment '*'
