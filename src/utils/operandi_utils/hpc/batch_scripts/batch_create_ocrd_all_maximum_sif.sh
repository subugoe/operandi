#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --time 02:00:00
#SBATCH --output /scratch1/projects/project_pwieder_ocr/batch_job_logs/batch_create_ocrd_all_sif_job-%J.txt
#SBATCH --cpus-per-task 16
#SBATCH --mem 64G

set -e

module purge
module load singularity

hostname
/opt/slurm/etc/scripts/misc/slurm_resources

SINGULARITY_CACHE_DIR="/scratch1/projects/project_pwieder_ocr"
SIF_NAME="ocrd_all_maximum_image.sif"
OCRD_ALL_MAXIMUM_IMAGE="docker://ocrd/all:latest"

cd "${SINGULARITY_CACHE_DIR}" || exit
singularity build --disable-cache "${SIF_NAME}" "${OCRD_ALL_MAXIMUM_IMAGE}"
singularity exec "${SIF_NAME}" ocrd --version
