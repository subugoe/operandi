#!/bin/bash
set -e

#SBATCH --partition medium
#SBATCH --constraint scratch
#SBATCH --output ./test-slurm-job-%J.txt
#SBATCH --cpus-per-task 2
#STABCH --mem 16G

hostname
slurm_resources

module purge
module load singularity

singularity exec "/scratch1/users/${USER}/ocrd_all_maximum_image.sif" ocrd --version
