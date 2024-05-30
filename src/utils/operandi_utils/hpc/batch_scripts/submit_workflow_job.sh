#!/bin/bash
#SBATCH --constraint scratch

set -e

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
BIND_OCRD_MODELS="${OCRD_MODELS_DIR}:${OCRD_MODELS_DIR_IN_DOCKER}"

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
# true/false flag to switch between using and not using a mets server
USE_METS_SERVER=${11}

WORKFLOW_JOB_DIR="${SCRATCH_BASE}/${WORKFLOW_JOB_ID}"
NF_SCRIPT_PATH="${WORKFLOW_JOB_DIR}/${NEXTFLOW_SCRIPT_ID}"
WORKSPACE_DIR="${WORKFLOW_JOB_DIR}/${WORKSPACE_ID}"
WORKSPACE_DIR_IN_DOCKER="/ws_data"
BIND_WORKSPACE_DIR="${WORKSPACE_DIR}:${WORKSPACE_DIR_IN_DOCKER}"
BIND_METS_FILE_PATH="${WORKSPACE_DIR_IN_DOCKER}/${METS_BASENAME}"
METS_SOCKET_BASENAME="mets_server.sock"
BIND_METS_SOCKET_PATH="${WORKSPACE_DIR_IN_DOCKER}/${METS_SOCKET_BASENAME}"

hostname
/opt/slurm/etc/scripts/misc/slurm_resources

module purge
module load singularity
module load nextflow
# module load spack-user; eval "$(spack load --sh curl%gcc@10.2.0)"

echo "ocrd all SIF path: $SIF_PATH"
echo "Workspace dir: $WORKSPACE_DIR"
echo "Nextflow script path: $NF_SCRIPT_PATH"
echo "Use mets server: $USE_METS_SERVER"
echo "Used file group: $IN_FILE_GRP"
echo "Pages: $PAGES"
singularity exec "$SIF_PATH" ocrd --version


# To submit separate jobs for each process in the NF script
# export NXF_EXECUTOR=slurm


# Define functions to be used
check_existence_of_paths () {
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
}

unzip_workflow_job_dir () {
  if [ ! -f "${WORKFLOW_JOB_DIR}.zip" ]; then
    echo "Required scratch slurm workspace zip is not available: ${WORKFLOW_JOB_DIR}.zip"
    exit 1
  fi

  echo "Unzipping ${WORKFLOW_JOB_DIR}.zip to: ${WORKFLOW_JOB_DIR}"
  unzip "${WORKFLOW_JOB_DIR}.zip" -d "${SCRATCH_BASE}" > "${SCRATCH_BASE}/${WORKSPACE_ID}_unzipping.log"
  echo "Removing zip: ${WORKFLOW_JOB_DIR}.zip"
  mv "${SCRATCH_BASE}/${WORKSPACE_ID}_unzipping.log" "${WORKFLOW_JOB_DIR}/workflow_job_unzipping.log"
  rm "${WORKFLOW_JOB_DIR}.zip"

  if [ ! -d "${WORKFLOW_JOB_DIR}" ]; then
    echo "Required scratch slurm workflow dir not available: ${WORKFLOW_JOB_DIR}"
    exit 1
  fi

  cd "${WORKFLOW_JOB_DIR}" || exit 1
}

start_mets_server () {
  # TODO: Would be better to start the mets server as an instance, but this is still broken
  # singularity instance start \
  #   --bind "${BIND_WORKSPACE_DIR}" \
  #   "${SIF_PATH}" \
  #   instance_mets_server \
  #  ocrd workspace -U "${BIND_METS_SOCKET_PATH}" -d "${WORKSPACE_DIR_IN_DOCKER}" server start

  if [ "$1" == "true" ] ; then
    echo "Starting the mets server for the specific workspace in the background"
    singularity exec \
      --bind "${BIND_WORKSPACE_DIR}" \
      "${SIF_PATH}" \
      ocrd workspace -U "${BIND_METS_SOCKET_PATH}" -d "${WORKSPACE_DIR_IN_DOCKER}" server start \
      > "${WORKSPACE_DIR}/mets_server.log" 2>&1 &
  fi
  sleep 5
}

stop_mets_server () {
  # Not supported in the HPC (the version there is <7.40)
  # curl -X DELETE --unix-socket "${WORKSPACE_DIR}/${METS_SOCKET_BASENAME}" "http://localhost/"

  # TODO Stop the instance here
  # singularity instance stop instance_mets_server

  if [ "$1" == "true" ] ; then
    echo "Stopping the mets server"
    singularity exec \
      --bind "${BIND_WORKSPACE_DIR}" \
      "${SIF_PATH}" \
      ocrd workspace -U "${BIND_METS_SOCKET_PATH}" -d "${WORKSPACE_DIR_IN_DOCKER}" server stop
  fi
}

execute_nextflow_workflow () {
  local SINGULARITY_CMD="singularity exec --bind ${BIND_WORKSPACE_DIR} --bind ${BIND_OCRD_MODELS} --env OCRD_METS_CACHING=false ${SIF_PATH}"
  if [ "$1" == "true" ] ; then
    echo "Executing the nextflow workflow with mets server"
    nextflow run "${NF_SCRIPT_PATH}" \
    -ansi-log false \
    -with-report \
    --input_file_group "${IN_FILE_GRP}" \
    --mets "${BIND_METS_FILE_PATH}" \
    --mets_socket "${BIND_METS_SOCKET_PATH}" \
    --workspace_dir "${WORKSPACE_DIR_IN_DOCKER}" \
    --pages "${PAGES}" \
    --singularity_wrapper "${SINGULARITY_CMD}" \
    --cpus "${CPUS}" \
    --ram "${RAM}" \
    --forks "${FORKS}"
  else
    echo "Executing the nextflow workflow without mets server"
    nextflow run "${NF_SCRIPT_PATH}" \
    -ansi-log false \
    -with-report \
    --input_file_group "${IN_FILE_GRP}" \
    --mets "${BIND_METS_FILE_PATH}" \
    --workspace_dir "${WORKSPACE_DIR_IN_DOCKER}" \
    --pages "${PAGES}" \
    --singularity_wrapper "${SINGULARITY_CMD}" \
    --cpus "${CPUS}" \
    --ram "${RAM}" \
    --forks "${FORKS}"
  fi

  # Useful for handling all kinds of exit status codes in the future
  case $? in
    0) echo "The nextflow workflow execution has finished successfully" ;;
    *) echo "The nextflow workflow execution has failed" >&2 exit 1 ;;
  esac
}

zip_results () {
  # Delete symlinks created for the Nextflow workers
  find "${WORKFLOW_JOB_DIR}" -type l -delete
  # Create a zip of the ocrd workspace dir
  cd "${WORKSPACE_DIR}" && zip -r "${WORKSPACE_ID}.zip" "." -x "*.sock" > "workspace_zipping.log"
  # Create a zip of the Nextflow run results by excluding the ocrd workspace dir
  cd "${WORKFLOW_JOB_DIR}" && zip -r "${WORKFLOW_JOB_ID}.zip" "." -x "${WORKSPACE_ID}**" > "workflow_job_zipping.log"
}

# Main loop for workflow job execution
check_existence_of_paths
unzip_workflow_job_dir
start_mets_server "$USE_METS_SERVER"
execute_nextflow_workflow "$USE_METS_SERVER"
stop_mets_server "$USE_METS_SERVER"
zip_results
