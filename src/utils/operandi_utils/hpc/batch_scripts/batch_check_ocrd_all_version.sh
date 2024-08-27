#!/bin/bash
#SBATCH --partition standard96:shared
#SBATCH --time 00:05:00
#SBATCH --qos 2h
#SBATCH --output check_ocrd_all_version_job-%J.txt
#SBATCH --cpus-per-task 1
#SBATCH --mem 16G

set -e

hostname
/opt/slurm/etc/scripts/misc/slurm_resources

module purge
module load apptainer
SIF_PATH="/mnt/lustre-emmy-hdd/projects/project_pwieder_ocr_nhr/ocrd_all_maximum_image.sif"

apptainer exec "$SIF_PATH" ocrd --version
apptainer exec "$SIF_PATH" ocrd-tesserocr-recognize --dump-module-dir
apptainer exec "$SIF_PATH" ls -la /models
