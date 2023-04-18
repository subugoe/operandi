#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 2
#SBATCH --mem 8G
#SBATCH --output /home/users/mmustaf/jobs_output/workflow-job-%J.txt

module purge
module load singularity
module load nextflow

SIF_PATH="/scratch1/users/mmustaf/ocrd_all_image_2023_04_17_1422.sif"

if [ ! -d "/scratch1/users/${USER}" ]; then
  mkdir -p "/scratch1/users/${USER}"
fi

TEMPDIR=$(mktemp -d "/scratch1/users/${USER}/XXXXXXXX")

if [ ! -d "${TEMPDIR}" ]; then
  echo "Temp directory was not created!"
  exit 1
fi

# copies the ocrd-workspace folder which holds the OCR-D-IMG folder and the mets file
# copies the Nextflow script - seq_ocrd_wf_single_processor.nf
cp -rf /home/users/mmustaf/workflow5/bin "${TEMPDIR}"

cd "${TEMPDIR}"/bin || exit

# Execute the Nextflow script
nextflow run seq_ocrd_wf_single_processor.nf \
--tempdir "${TEMPDIR}"/bin \
--sif_path ${SIF_PATH} \
--input_file_group "OCR-D-IMG" \
--mets "${TEMPDIR}"/bin/ocrd-workspace/mets.xml

hostname
slurm_resources

mv "${TEMPDIR}" /home/users/mmustaf/ocrd-results
rm -rf "${TEMPDIR}"
