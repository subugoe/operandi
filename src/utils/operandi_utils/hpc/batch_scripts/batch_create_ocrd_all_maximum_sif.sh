#!/bin/bash
#SBATCH --partition standard96:shared
#SBATCH --time 2:00:00
#SBATCH --output create_ocrd_all_sif_job-%J.txt
#SBATCH --cpus-per-task 16
#SBATCH --mem 64G

set -e

module purge
module load apptainer

hostname
/opt/slurm/etc/scripts/misc/slurm_resources

APPTAINER_TMPDIR="$LOCAL_TMPDIR"
APPTAINER_CACHE_DIR="/mnt/lustre-emmy-hdd/projects/project_pwieder_ocr_nhr"
SIF_NAME="ocrd_all_maximum_image_new.sif"
OCRD_ALL_MAXIMUM_IMAGE="docker://ocrd/all:latest"

cd "${APPTAINER_CACHE_DIR}" || exit
apptainer build --disable-cache "${SIF_NAME}" "${OCRD_ALL_MAXIMUM_IMAGE}"
apptainer exec "${SIF_NAME}" ocrd --version
