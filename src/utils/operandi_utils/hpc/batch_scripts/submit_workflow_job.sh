#!/bin/bash
#SBATCH --constraint scratch

# Parameters are as follows:
# S0 - This batch script
# S1 - The scratch base for slurm workspaces
# $2 - Workflow job id
# $3 - Nextflow script id
# $4 - Entry input file group
# $5 - Workspace id
# $6 - Mets basename - default "mets.xml"
# $7 - CPUs for the Nextflow processes
# $8 - RAM for the Nextflow processes
# $9 - Amount of forks per OCR-D processor in the NF script
# $10 - Amount of pages in the workspace

SIF_PATH="/scratch1/users/${USER}/ocrd_all_maximum_image.sif"
OCRD_MODELS_DIR="/scratch1/users/${USER}/ocrd_models"
OCRD_MODELS_DIR_IN_DOCKER="/usr/local/share"

SCRATCH_BASE=$1
WORKFLOW_JOB_ID=$2
NEXTFLOW_SCRIPT_ID=$3
IN_FILE_GRP=$4
WORKSPACE_ID=$5
METS_BASENAME=$6
CPUS=$7
RAM=$8
FORKS=$9
PAGES=${10}

WORKFLOW_JOB_DIR="${SCRATCH_BASE}/${WORKFLOW_JOB_ID}"
WORKSPACE_DIR="${WORKFLOW_JOB_DIR}/${WORKSPACE_ID}"
NF_SCRIPT_PATH="${WORKFLOW_JOB_DIR}/${NEXTFLOW_SCRIPT_ID}"
METS_SOCKET_BASENAME="mets_server.sock"

hostname
slurm_resources

module purge
module load singularity
module load nextflow
# module load spack-user; eval "$(spack load --sh curl%gcc@10.2.0)"

# To submit separate jobs for each process in the NF script
# export NXF_EXECUTOR=slurm

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

if [ ! -f "${WORKFLOW_JOB_DIR}.zip" ]; then
  echo "Required scratch slurm workspace zip is not available: ${WORKFLOW_JOB_DIR}.zip"
  exit 1
else
  echo "Unzipping ${WORKFLOW_JOB_DIR}.zip to: ${WORKFLOW_JOB_DIR}"
  unzip "${WORKFLOW_JOB_DIR}.zip" -d "${SCRATCH_BASE}" > "${SCRATCH_BASE}/workflow_job_unzipping.log"
  echo "Removing zip: ${WORKFLOW_JOB_DIR}.zip"
  mv "${SCRATCH_BASE}/workflow_job_unzipping.log" "${WORKFLOW_JOB_DIR}/workflow_job_unzipping.log"
  rm "${WORKFLOW_JOB_DIR}.zip"
fi

if [ ! -d "${WORKFLOW_JOB_DIR}" ]; then
  echo "Required scratch slurm workflow dir not available: ${WORKFLOW_JOB_DIR}"
  exit 1
else
  cd "${WORKFLOW_JOB_DIR}" || exit 1
fi

# TODO: Would be better to start the mets server as an instance, but this is still broken
# singularity instance start \
#   --bind "${WORKSPACE_DIR}:/ws_data" \
#   "${SIF_PATH}" \
#   instance_mets_server \
#  ocrd workspace -U "/ws_data/${METS_SOCKET_BASENAME}" -d "/ws_data" server start

# Start the mets server for the specific workspace in the background
singularity exec \
  --bind "${WORKSPACE_DIR}:/ws_data" \
  "${SIF_PATH}" \
  ocrd workspace -U "/ws_data/${METS_SOCKET_BASENAME}" -d "/ws_data" server start \
  > "${WORKSPACE_DIR}/mets_server.log" 2>&1 &

sleep 7

# Execute the Nextflow script
nextflow run "${NF_SCRIPT_PATH}" \
-ansi-log false \
-with-report \
--input_file_group "${IN_FILE_GRP}" \
--mets "/ws_data/${METS_BASENAME}" \
--mets_socket "/ws_data/${METS_SOCKET_BASENAME}" \
--workspace_dir "/ws_data" \
--pages "${PAGES}" \
--singularity_wrapper "singularity exec --bind ${WORKSPACE_DIR}:/ws_data --bind ${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER} --env OCRD_METS_CACHING=true ${SIF_PATH}" \
--cpus "${CPUS}" \
--ram "${RAM}" \
--forks "${FORKS}"

# Not supported in the HPC (the version there is <7.40)
# curl -X DELETE --unix-socket "${WORKSPACE_DIR}/${METS_SOCKET_BASENAME}" "http://localhost/"

# TODO Stop the instance here
# singularity instance stop instance_mets_server

# Stop the mets server started above
singularity exec \
  --bind "${WORKSPACE_DIR}:/ws_data" \
  "${SIF_PATH}" \
  ocrd workspace -U "/ws_data/${METS_SOCKET_BASENAME}" -d "/ws_data" server stop

# Delete symlinks created for the Nextflow workers
find "${WORKFLOW_JOB_DIR}" -type l -delete
# Create a zip of the ocrd workspace dir
cd "${WORKSPACE_DIR}" && zip -r "${WORKSPACE_ID}.zip" "." -x "*.sock" > "workspace_zipping.log"
# Create a zip of the Nextflow run results by excluding the ocrd workspace dir
cd "${WORKFLOW_JOB_DIR}" && zip -r "${WORKFLOW_JOB_ID}.zip" "." -x "${WORKSPACE_ID}**" > "workflow_job_zipping.log"
