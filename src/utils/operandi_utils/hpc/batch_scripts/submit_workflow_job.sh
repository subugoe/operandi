#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 1
#SBATCH --mem 64G
#SBATCH --time 48:00:00
#SBATCH --output /scratch1/users/mmustaf/operandi/slurm-job-%J.txt

# Parameters are as follows:
# S0 - This batch script
# $1 - Workflow job id
# $2 - Nextflow script id
# $3 - Entry input file group
# $4 - Workspace id
# $5 - Mets basename - default "mets.xml"

SIF_PATH="/scratch1/users/${USER}/ocrd_all_maximum_image.sif"
SCRATCH_BASE="/scratch1/users/${USER}/operandi/slurm_workspaces"
OCRD_MODELS_DIR="/scratch1/users/${USER}/ocrd_models"
OCRD_MODELS_DIR_IN_DOCKER="/usr/local/share"

WORKFLOW_JOB_ID=$1
NEXTFLOW_SCRIPT_ID=$2
IN_FILE_GRP=$3
WORKSPACE_ID=$4
METS_BASENAME=$5

SCRATCH_SLURM_DIR_PATH="${SCRATCH_BASE}/${WORKFLOW_JOB_ID}"

NF_SCRIPT_PATH="${SCRATCH_SLURM_DIR_PATH}/${NEXTFLOW_SCRIPT_ID}"
WORKSPACE_DIR_PATH="${SCRATCH_SLURM_DIR_PATH}/${WORKSPACE_ID}"
METS_PATH="${WORKSPACE_DIR_PATH}/${METS_BASENAME}"

hostname
slurm_resources

module purge
module load singularity
module load nextflow

# To submit separate jobs for each process in the NF script
export NXF_EXECUTOR=slurm

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

# Execute the Nextflow script
nextflow run "${NF_SCRIPT_PATH}" \
-ansi-log false \
-with-report \
--input_file_group "${IN_FILE_GRP}" \
--mets "${METS_PATH}" \
--singularity_wrapper "singularity exec --bind ${SCRATCH_SLURM_DIR_PATH} --bind ${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER} --env OCRD_METS_CACHING=true ${SIF_PATH}" \
--cpus 1

# Delete symlinks created for the Nextflow workers
find "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" -type l -delete
# Create a zip of the ocrd workspace dir
cd "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}/${WORKSPACE_ID}" && zip -r "${WORKSPACE_ID}.zip" "."
# Create a zip of the Nextflow run results by excluding the ocrd workspace dir
cd "${SCRATCH_BASE}/${WORKFLOW_JOB_ID}" && zip -r "${WORKFLOW_JOB_ID}.zip" "." -x "${WORKSPACE_ID}**"
