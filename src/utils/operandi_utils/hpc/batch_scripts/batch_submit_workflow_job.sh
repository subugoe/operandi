#!/bin/bash

set -e

module purge
module load jq
module load apptainer
module load nextflow
# module load spack-user; eval "$(spack load --sh curl%gcc@10.2.0)"

hostname
# /opt/slurm/etc/scripts/misc/slurm_resource

# To submit separate jobs for each process in the NF script
# export NXF_EXECUTOR=slurm

json_args="$1"
SCRATCH_BASE=$(echo "$json_args" | jq .scratch_base_dir | tr -d '"')
WORKFLOW_JOB_ID=$(echo "$json_args" | jq .workflow_job_id | tr -d '"')
NEXTFLOW_SCRIPT_ID=$(echo "$json_args" | jq .nextflow_script_id | tr -d '"')
IN_FILE_GRP=$(echo "$json_args" | jq .input_file_group | tr -d '"')
WORKSPACE_ID=$(echo "$json_args" | jq .workspace_id | tr -d '"')
METS_BASENAME=$(echo "$json_args" | jq .mets_basename | tr -d '"')
CPUS=$(echo "$json_args" | jq .cpus | tr -d '"')
RAM=$(echo "$json_args" | jq .ram | tr -d '"')
FORKS=$(echo "$json_args" | jq .nf_process_forks | tr -d '"')
PAGES=$(echo "$json_args" | jq .ws_pages_amount | tr -d '"')
USE_METS_SERVER=$(echo "$json_args" | jq .use_mets_server_bash_flag | tr -d '"')
FILE_GROUPS_TO_REMOVE=$(echo "$json_args" | jq .file_groups_to_remove | tr -d '"')

SIF_PATH="/mnt/lustre-emmy-hdd/projects/project_pwieder_ocr_nhr/ocrd_all_maximum_image.sif"
SIF_PATH_IN_NODE="${TMP_LOCAL}/ocrd_all_maximum_image.sif"
OCRD_MODELS_DIR="/mnt/lustre-emmy-hdd/projects/project_pwieder_ocr_nhr/ocrd_models"
OCRD_MODELS_DIR_IN_NODE="${TMP_LOCAL}/ocrd_models"
OCRD_MODELS_DIR_IN_DOCKER="/usr/local/share/ocrd-resources"
BIND_OCRD_MODELS="${OCRD_MODELS_DIR_IN_NODE}/ocrd-resources:${OCRD_MODELS_DIR_IN_DOCKER}"

WORKFLOW_JOB_DIR="${SCRATCH_BASE}/${WORKFLOW_JOB_ID}"
NF_SCRIPT_PATH="${WORKFLOW_JOB_DIR}/${NEXTFLOW_SCRIPT_ID}"
WORKSPACE_DIR="${WORKFLOW_JOB_DIR}/${WORKSPACE_ID}"
WORKSPACE_DIR_IN_DOCKER="/ws_data"
BIND_WORKSPACE_DIR="${WORKSPACE_DIR}:${WORKSPACE_DIR_IN_DOCKER}"
BIND_METS_FILE_PATH="${WORKSPACE_DIR_IN_DOCKER}/${METS_BASENAME}"
METS_SOCKET_BASENAME="mets_server.sock"
BIND_METS_SOCKET_PATH="${WORKSPACE_DIR_IN_DOCKER}/${METS_SOCKET_BASENAME}"

echo "ocrd all SIF path: $SIF_PATH"
echo "ocrd all SIF path node local: $SIF_PATH_IN_NODE"
echo "Workspace dir: $WORKSPACE_DIR"
echo "Nextflow script path: $NF_SCRIPT_PATH"
echo "Use mets server: $USE_METS_SERVER"
echo "Used file group: $IN_FILE_GRP"
echo "Pages: $PAGES"

# Define functions to be used
check_existence_of_paths() {
  # The SIF file of the OCR-D All docker image must be previously created
  if [ ! -f "${SIF_PATH}" ]; then
    echo "Required ocrd_all_image sif file not found at: ${SIF_PATH}"
    exit 1
  fi
  echo "Required ocrd_all_image sif file found at: ${SIF_PATH}"

  # Models directory must be previously filled with OCR-D models
  if [ ! -d "${OCRD_MODELS_DIR}" ]; then
    echo "Ocrd models directory not found at: ${OCRD_MODELS_DIR}"
    exit 1
  fi
  echo "Ocrd models directory found at: ${OCRD_MODELS_DIR}"

  if [ ! -d "${SCRATCH_BASE}" ]; then
    mkdir -p "${SCRATCH_BASE}"
  fi

  if [ ! -d "${SCRATCH_BASE}" ]; then
    echo "Required scratch base dir was not created: ${SCRATCH_BASE}"
    exit 1
  fi
  echo "Scratch base found/created at: ${SCRATCH_BASE}"
}

clear_data_from_computing_node() {
  echo "If existing, removing the SIF from the computing node, path: ${SIF_PATH_IN_NODE}"
  rm -f "${SIF_PATH_IN_NODE}"
  echo "If existing, removing the OCR-D models from the computing node, path: ${OCRD_MODELS_DIR_IN_NODE}"
  rm -rf "${OCRD_MODELS_DIR_IN_NODE}"
}

transfer_requirements_to_node_storage() {
  cp "${SIF_PATH}" "${SIF_PATH_IN_NODE}"
  # Check if transfer successful
  if [ ! -f "${SIF_PATH_IN_NODE}" ]; then
    echo "Required ocrd_all_image sif file not found at node local storage: ${SIF_PATH_IN_NODE}"
    exit 1
  else
    echo "Successfully transferred SIF to node local storage"
    apptainer exec "$SIF_PATH_IN_NODE" ocrd --version
  fi

  cp -R "${OCRD_MODELS_DIR}" "${OCRD_MODELS_DIR_IN_NODE}"
  if [ ! -d "${OCRD_MODELS_DIR_IN_NODE}" ]; then
    echo "Ocrd models directory not found at node local storage: ${OCRD_MODELS_DIR_IN_NODE}"
    clear_data_from_computing_node
    exit 1
  else
    echo "Successfully transferred ocrd models to node local storage"
  fi
}

unzip_workflow_job_dir() {
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

start_mets_server() {
  if [ "$1" == "true" ] ; then
    echo "Starting the mets server for the specific workspace in the background"
    apptainer exec \
      --bind "${BIND_WORKSPACE_DIR}" \
      "${SIF_PATH_IN_NODE}" \
      ocrd workspace -U "${BIND_METS_SOCKET_PATH}" -d "${WORKSPACE_DIR_IN_DOCKER}" server start \
      > "${WORKSPACE_DIR}/mets_server.log" 2>&1 &
  fi
  sleep 10
}

stop_mets_server() {
  if [ "$1" == "true" ] ; then
    echo "Stopping the mets server"
    apptainer exec \
      --bind "${BIND_WORKSPACE_DIR}" \
      "${SIF_PATH_IN_NODE}" \
      ocrd workspace -U "${BIND_METS_SOCKET_PATH}" -d "${WORKSPACE_DIR_IN_DOCKER}" server stop
  fi
}

execute_nextflow_workflow() {
  local APPTAINER_CMD="apptainer exec --bind ${BIND_WORKSPACE_DIR} --bind ${BIND_OCRD_MODELS} --env OCRD_METS_CACHING=false ${SIF_PATH_IN_NODE}"
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
    --singularity_wrapper "${APPTAINER_CMD}" \
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
    --singularity_wrapper "${APPTAINER_CMD}" \
    --cpus "${CPUS}" \
    --ram "${RAM}" \
    --forks "${FORKS}"
  fi

  case $? in
    0) echo "The nextflow workflow execution has finished successfully" ;;
    *) echo "The nextflow workflow execution has failed" >&2 clear_data_from_computing_node exit 1 ;;
  esac
}

list_file_groups_from_workspace() {
    all_file_groups=()
    mapfile -t all_file_groups < <(apptainer exec --bind "${BIND_WORKSPACE_DIR}" "${SIF_PATH_IN_NODE}" ocrd workspace -d "${WORKSPACE_DIR_IN_DOCKER}" list-group)
    file_groups_length=${#all_file_groups[@]}
    echo -n "File groups: "
    for file_group in "${all_file_groups[@]}"
    do
       echo -n "${file_group} "
    done
    echo "Total amount of file groups detected: $file_groups_length"
    echo
}

remove_file_group_from_workspace() {
  echo "Removing file group: $1"
  apptainer exec --bind "${BIND_WORKSPACE_DIR}" "${SIF_PATH_IN_NODE}" \
  ocrd workspace -d "${WORKSPACE_DIR_IN_DOCKER}" remove-group -r -f "$1" \
  > "${WORKSPACE_DIR}/remove_file_groups.log" 2>&1
}

remove_file_groups_from_workspace() {
  list_file_groups_from_workspace
  if [ "$1" != "" ] ; then
    echo "Splitting file groups to an array"
    file_groups=()
    mapfile -t file_groups < <(echo "$1" | tr "," "\n")
    for file_group in "${file_groups[@]}"
    do
      remove_file_group_from_workspace "$file_group"
    done
    list_file_groups_from_workspace
    case $? in
      0) echo "The file groups have been removed successfully" ;;
      *) echo "The file groups removal has failed" >&2 clear_data_from_computing_node exit 1 ;;
    esac
  else
    echo "No file groups were requested to be removed"
  fi
}

zip_results() {
  # Delete symlinks created for the Nextflow workers
  find "${WORKFLOW_JOB_DIR}" -type l -delete
  # Create a zip of the ocrd workspace dir
  cd "${WORKSPACE_DIR}" && zip -r "${WORKSPACE_ID}.zip" "." -x "*.sock" > "workspace_zipping.log"
  # Create a zip of the Nextflow run results by excluding the ocrd workspace dir
  cd "${WORKFLOW_JOB_DIR}" && zip -r "${WORKFLOW_JOB_ID}.zip" "." -x "${WORKSPACE_ID}**" > "workflow_job_zipping.log"

  case $? in
    0) echo "The results have been zipped successfully" ;;
    *) echo "The zipping of results has failed" >&2 clear_data_from_computing_node exit 1 ;;
  esac
}


# Main loop for workflow job execution
check_existence_of_paths
unzip_workflow_job_dir
transfer_requirements_to_node_storage
start_mets_server "$USE_METS_SERVER"
execute_nextflow_workflow "$USE_METS_SERVER"
stop_mets_server "$USE_METS_SERVER"
remove_file_groups_from_workspace "$FILE_GROUPS_TO_REMOVE"
zip_results
clear_data_from_computing_node
