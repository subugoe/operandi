#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 4
#SBATCH --mem 32G
#SBATCH --output /home/users/mmustaf/jobs_output/job-%J.txt

module purge
module load singularity # loads "git" and "go" as well
module load nextflow # loads "openjdk" as well


if [ ! -d "/scratch1/users/${USER}" ]; then
  mkdir "/scratch1/users/${USER}"
fi

TEMPDIR=$(mktemp -d "/scratch1/users/${USER}/XXXXXXXX")

if [ ! -d "${TEMPDIR}" ]; then
  echo "Temp directory was not created!"
  exit 1
fi

# copies the ocrd-workspace folder which holds the OCR-D-IMG folder and the mets file
# copies the Nextflow script - seq_ocrd_wf_single_processor.nf
cp -rf /home/users/mmustaf/workflow5/bin ${TEMPDIR}

cd ${TEMPDIR}/bin

# Execute the Nextflow script
nextflow run seq_ocrd_wf_single_processor.nf --tempdir ${TEMPDIR}/bin

hostname
slurm_resources

# rm -rf $TEMPDIR
