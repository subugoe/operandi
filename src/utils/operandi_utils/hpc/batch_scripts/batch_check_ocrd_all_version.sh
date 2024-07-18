#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --time 0:05:00
#SBATCH --output /scratch1/projects/project_pwieder_ocr/batch_job_logs/batch_check_ocrd_all_version_job-%J.txt
#SBATCH --cpus-per-task 1
#STABCH --mem 16G

set -e

hostname
/opt/slurm/etc/scripts/misc/slurm_resources

module purge
module load singularity

singularity exec "/scratch1/projects/project_pwieder_ocr/ocrd_all_maximum_image.sif" ocrd --version
