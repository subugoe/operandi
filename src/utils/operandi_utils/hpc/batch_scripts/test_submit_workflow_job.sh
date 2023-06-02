#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 2
#SBATCH --mem 2G
#SBATCH --output ./operandi_tests/test-slurm-job-%J.txt

# Parameters are as follows:
# S0 - This batch script
# $1 - Workflow job id
# $2 - Nextflow script id
# $3 - Entry input file group
# $4 - Workspace id

SIF_PATH="/scratch1/users/${USER}/ocrd_all_maximum_image.sif"
HOME_BASE="/home/users/${USER}/operandi_tests/slurm_workspaces"
SCRATCH_BASE="/scratch1/users/${USER}/operandi_tests/slurm_workspaces"
OCRD_MODELS_DIR="/scratch1/users/${USER}/ocrd_models"
OCRD_MODELS_DIR_IN_DOCKER="/usr/local/share"

WORKFLOW_JOB_ID=$1
NEXTFLOW_SCRIPT_ID=$2
IN_FILE_GRP=$3
WORKSPACE_ID=$4

hostname
slurm_resources

module purge
module load singularity
module load nextflow

# The SIF file of the OCR-D All docker image must be previously created
if [ ! -f "${SIF_PATH}" ]; then
  echo "Required ocrd_all_image sif file not found at: ${SIF_PATH}"
  exit 1
fi

# Models directory must be previously filled with OCR-D models
if [ ! -d "${OCRD_MODELS_DIR}" ]; then
  echo "Ocrd models directory not found at: ${OCRD_MODELS_DIR}"
  exit 1
fi

if [ ! -d "${SCRATCH_BASE}" ]; then
  mkdir -p "${SCRATCH_BASE}"
fi

if [ ! -d "${SCRATCH_BASE}" ]; then
  echo "Required scratch base dir was not created: ${SCRATCH_BASE}"
  exit 1
fi

if [ ! -f "${HOME_BASE}/${WORKFLOW_JOB_ID}.zip" ]; then
  echo "Required slurm workspace zip is not available: ${HOME_BASE}/${WORKFLOW_JOB_ID}.zip"
  exit 1
else
  mv "${HOME_BASE}/${WORKFLOW_JOB_ID}.zip" "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}.zip"
  unzip "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}.zip" -d "${SCRATCH_BASE}"
  rm "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}.zip"
fi

if [ ! -d "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" ]; then
  echo "Dir not available: ${SCRATCH_BASE}/${WORKFLOW_JOB_ID}"
  exit 1
else
  cd "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" || exit 1
fi

# Execute the Nextflow script
nextflow run "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}/${NEXTFLOW_SCRIPT_ID}" \
-ansi-log false \
-with-report \
--volume_map_dir "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" \
--models_mapping "${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}" \
--sif_path "${SIF_PATH}" \
--input_file_group "${IN_FILE_GRP}" \
--mets "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}/${WORKSPACE_ID}/mets.xml"

# Delete symlinks created for the Nextflow workers
find "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" -type l -delete
# Move the slurm workspace dir to home base
mv "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" "${HOME_BASE}"
# Create a zip of the ocrd workspace dir
cd "${HOME_BASE}/${WORKFLOW_JOB_ID}/${WORKSPACE_ID}" && zip -r "${WORKSPACE_ID}.zip" "."
# Create a zip of the Nextflow run results by excluding the ocrd workspace dir
cd "${HOME_BASE}/${WORKFLOW_JOB_ID}" && zip -r "${WORKFLOW_JOB_ID}.zip" "." -x "${WORKSPACE_ID}**"
