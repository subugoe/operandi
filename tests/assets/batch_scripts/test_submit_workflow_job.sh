#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 1
#SBATCH --mem 1G
#SBATCH --output ./tests/workflow_jobs/test_workflow-job-%J.txt

# Parameters are as follows:
# S0 - This batch script
# $1 - Workflow job id
# $2 - Nextflow script id
# $3 - Entry input file group

WORKFLOW_JOB_ID=$1
NEXTFLOW_SCRIPT_ID=$2
IN_FILE_GRP=$3

hostname
slurm_resources

module purge
module load singularity
module load nextflow

SIF_PATH="/scratch1/users/mmustaf/ocrd_all_image_2023_04_17_1422.sif"
HOME_BASE="/home/users/${USER}/tests/workflow_jobs"
SCRATCH_BASE="/scratch1/users/${USER}/tests/workflow_jobs"

if [ ! -d "${SCRATCH_BASE}" ]; then
  mkdir -p "${SCRATCH_BASE}"
fi

if [ ! -d "${SCRATCH_BASE}" ]; then
  echo "Required test scratch base dir was not created: ${SCRATCH_BASE}"
  exit 1
fi

mv "${HOME_BASE}/${WORKFLOW_JOB_ID}" "${SCRATCH_BASE}"

# shellcheck disable=SC2164
cd "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}"

# Execute the Nextflow script
nextflow run "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}/${NEXTFLOW_SCRIPT_ID}" \
-ansi-log false \
-with-report \
--volume_map_dir "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" \
--sif_path ${SIF_PATH} \
--input_file_group "${IN_FILE_GRP}" \
--mets "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}/data/mets.xml"

# Delete symlinks created for the Nextflow workers
find "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" -type l -delete
mv "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" "${HOME_BASE}"
