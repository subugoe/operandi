#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 2
#SBATCH --mem 2G
#SBATCH --output /scratch1/users/mmustaf/operandi_tests/test-slurm-job-%J.txt

# Parameters are as follows:
# S0 - This batch script
# $1 - Workflow job id
# $2 - Nextflow script id
# $3 - Entry input file group
# $4 - Workspace id
# $5 - Mets basename - default "mets.xml"

SIF_PATH="/scratch1/users/${USER}/ocrd_all_maximum_image.sif"
SCRATCH_BASE="/scratch1/users/${USER}/operandi_tests/slurm_workspaces"
OCRD_MODELS_DIR="/scratch1/users/${USER}/ocrd_models"
OCRD_MODELS_DIR_IN_DOCKER="/usr/local/share"

WORKFLOW_JOB_ID=$1
NEXTFLOW_SCRIPT_ID=$2
IN_FILE_GRP=$3
WORKSPACE_ID=$4
METS_BASENAME=$5

SCRATCH_SLURM_DIR_PATH="${SCRATCH_BASE}/${WORKFLOW_JOB_ID}"

NF_SCRIPT_PATH="${SCRATCH_SLURM_DIR_PATH}/${NEXTFLOW_SCRIPT_ID}"
METS_PATH="${SCRATCH_SLURM_DIR_PATH}/${WORKSPACE_ID}/${METS_BASENAME}"

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
  if [ ! -d "${SCRATCH_BASE}" ]; then
    echo "Required scratch base dir was not created: ${SCRATCH_BASE}"
    exit 1
  fi
fi

if [ ! -f "${SCRATCH_SLURM_DIR_PATH}.zip" ]; then
  echo "Required scratch slurm workspace zip is not available: ${SCRATCH_SLURM_DIR_PATH}.zip"
  exit 1
else
  echo "Unzipping ${SCRATCH_SLURM_DIR_PATH}.zip to: ${SCRATCH_SLURM_DIR_PATH}"
  unzip "${SCRATCH_SLURM_DIR_PATH}.zip" -d "${SCRATCH_BASE}"
  echo "Removing zip: ${SCRATCH_SLURM_DIR_PATH}.zip"
  rm "${SCRATCH_SLURM_DIR_PATH}.zip"
fi

if [ ! -d "${SCRATCH_SLURM_DIR_PATH}" ]; then
  echo "Required scratch slurm dir not available: ${SCRATCH_SLURM_DIR_PATH}"
  exit 1
else
  cd "${SCRATCH_SLURM_DIR_PATH}" || exit 1
fi

echo "Sif file path: ${SIF_PATH}"
echo "About to start workflow with script: ${NF_SCRIPT_PATH}"
echo "Mets path: ${METS_PATH}"
echo "Input file: ${IN_FILE_GRP}"
echo "Ocrd models mapping: ${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}"


# Execute the Nextflow script
nextflow run "${NF_SCRIPT_PATH}" \
-ansi-log false \
-with-report \
--volume_map_dir "${SCRATCH_SLURM_DIR_PATH}" \
--models_mapping "${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}" \
--sif_path "${SIF_PATH}" \
--input_file_group "${IN_FILE_GRP}" \
--mets "${METS_PATH}"

# Delete symlinks created for the Nextflow workers
find "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" -type l -delete
# Create a zip of the ocrd workspace dir
cd "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}/${WORKSPACE_ID}" && zip -r "${WORKSPACE_ID}.zip" "."
# Create a zip of the Nextflow run results by excluding the ocrd workspace dir
cd "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" && zip -r "${WORKFLOW_JOB_ID}.zip" "." -x "${WORKSPACE_ID}**"
