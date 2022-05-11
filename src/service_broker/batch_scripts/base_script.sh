#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 4
#SBATCH --mem 16G
#SBATCH --output /home/users/mmustaf/jobs_output/job-%J.txt

# clear the environment then load singularity and nextflow
module purge
module load singularity # loads "git" and "go" as well
module load nextflow # loads "openjdk" as well

# Check if scratch contains username folder
# If not, create it
if [ ! -d "/scratch1/users/${USER}" ]; then
  mkdir "/scratch1/users/${USER}"
fi

# Create a temporary directory with a random name
TEMPDIR=$(mktemp -d "/scratch1/users/${USER}/XXXXXXXX")

# Check if created
if [ ! -d "${TEMPDIR}" ]; then
  echo "Temp directory was not created!"
  exit 1
fi

# copies the ocrd-workspace folder which holds the OCR-D-IMG folder and the mets file
# copies the Nextflow script - seq_ocrd_wf_single_processor.nf
cp -rf /home/users/mmustaf/test1/bin ${TEMPDIR}

cd ${TEMPDIR}/bin

# execute the main Nextflow script
nextflow run seq_ocrd_wf_single_processor.nf --tempdir ${TEMPDIR}/bin

/usr/bin/hostname
/opt/slurm/bin/slurm_resources

# rm -rf $TEMPDIR
