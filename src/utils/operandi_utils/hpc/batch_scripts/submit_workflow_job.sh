#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 32
#SBATCH --mem 64G
#SBATCH --time 24:00:00
#SBATCH --output ./operandi/slurm-job-%J.txt

# Parameters are as follows:
# S0 - This batch script
# $1 - Workflow job id
# $2 - Nextflow script id
# $3 - Entry input file group
# $4 - Workspace id
# $5 - Mets basename - default "mets.xml"

SIF_PATH="/scratch1/users/${USER}/ocrd_all_maximum_image.sif"
HOME_BASE="/home/users/${USER}/operandi/slurm_workspaces"
SCRATCH_BASE="/scratch1/users/${USER}/operandi/slurm_workspaces"
OCRD_MODELS_DIR="/scratch1/users/${USER}/ocrd_models"
OCRD_MODELS_DIR_IN_DOCKER="/usr/local/share"

WORKFLOW_JOB_ID=$1
NEXTFLOW_SCRIPT_ID=$2
IN_FILE_GRP=$3
WORKSPACE_ID=$4
METS_BASENAME=$5

HOME_SLURM_DIR_PATH="${HOME_BASE}/${WORKFLOW_JOB_ID}"
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

if [ ! -f "${HOME_SLURM_DIR_PATH}.zip" ]; then
  echo "Required home slurm workspace zip is not available: ${HOME_SLURM_DIR_PATH}.zip"
  exit 1
else
  echo "Moving slurm workspace zip from: ${HOME_SLURM_DIR_PATH}.zip, to: ${SCRATCH_SLURM_DIR_PATH}.zip"
  mv "${HOME_SLURM_DIR_PATH}.zip" "${SCRATCH_SLURM_DIR_PATH}.zip"
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
# Move the slurm workspace dir to home base
mv "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" "${HOME_BASE}"
# Create a zip of the ocrd workspace dir
cd "${HOME_BASE}/${WORKFLOW_JOB_ID}/${WORKSPACE_ID}" && zip -r "${WORKSPACE_ID}.zip" "."
# Create a zip of the Nextflow run results by excluding the ocrd workspace dir
cd "${HOME_BASE}/${WORKFLOW_JOB_ID}" && zip -r "${WORKFLOW_JOB_ID}.zip" "." -x "${WORKSPACE_ID}**"
