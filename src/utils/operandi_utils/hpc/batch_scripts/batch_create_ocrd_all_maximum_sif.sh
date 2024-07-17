#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 32
#SBATCH --mem 64G
#SBATCH --time 240
#SBATCH --output /scratch1/projects/project_pwieder_ocr/batch_job_logs/create_ocrd_all_sif_job-%J.txt

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
