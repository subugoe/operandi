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

# TODO: Use the -r (or --raw-output) option to emit raw strings as output:
json_args="$1"

ocrd_processor_images=()
mapfile -t ocrd_processor_images < <(echo "$json_args" | jq .ocrd_processor_images | tr -d '"' | tr "," "\n")
echo "Ocrd total images in request: ${#ocrd_processor_images[@]}"
echo "Ocrd images: "
for ocrd_image in "${ocrd_processor_images[@]}"
do
   echo -n "${ocrd_image} "
done

PROJECT_BASE_DIR=$(echo "$json_args" | jq .project_base_dir | tr -d '"')
SCRATCH_BASE=$(echo "$json_args" | jq .scratch_base_dir | tr -d '"')
USE_METS_SERVER=$(echo "$json_args" | jq .use_mets_server | tr -d '"')
WORKFLOW_JOB_ID=$(echo "$json_args" | jq .workflow_job_id | tr -d '"')
WORKSPACE_ID=$(echo "$json_args" | jq .workspace_id | tr -d '"')
NF_SCRIPT_ID=$(echo "$json_args" | jq .nf_script_id | tr -d '"')
FILE_GROUPS_TO_REMOVE=$(echo "$json_args" | jq .file_groups_to_remove | tr -d '"')
SIF_OCRD_CORE=$(echo "$json_args" | jq .sif_ocrd_core | tr -d '"')
NF_RUN_COMMAND=$(echo "$json_args" | jq .nf_run_command | tr -d '"')

WORKFLOW_JOB_ZIP="$SCRATCH_BASE/$WORKFLOW_JOB_ID.zip"

NODE_DIR_BASE="$LOCAL_TMPDIR"
NODE_WORKFLOW_JOB_DIR="$NODE_DIR_BASE/$WORKFLOW_JOB_ID"
NODE_WORKFLOW_JOB_ZIP="$NODE_DIR_BASE/$WORKFLOW_JOB_ID.zip"
NODE_WORKSPACE_DIR="$NODE_DIR_BASE/$WORKFLOW_JOB_ID/$WORKSPACE_ID"
NODE_NF_SCRIPT_PATH="$NODE_DIR_BASE/$WORKFLOW_JOB_ID/$NF_SCRIPT_ID"

PROJECT_DIR_OCRD_MODELS="$PROJECT_BASE_DIR/ocrd_models"
PROJECT_DIR_PROCESSOR_SIFS="$PROJECT_BASE_DIR/ocrd_processor_sifs"
NODE_DIR_OCRD_MODELS="$NODE_DIR_BASE/ocrd_models"
NODE_DIR_PROCESSOR_SIFS="$NODE_DIR_BASE/ocrd_processor_sifs"
PATH_SIF_OCRD_CORE="$NODE_DIR_PROCESSOR_SIFS/$SIF_OCRD_CORE"

echo ""
echo "Project dir ocrd models: $PROJECT_DIR_OCRD_MODELS"
echo "Project dir processor sifs: $PROJECT_DIR_PROCESSOR_SIFS"
echo "Node dir ocrd models: $NODE_DIR_OCRD_MODELS"
echo "Node dir processor sifs: $NODE_DIR_PROCESSOR_SIFS"
echo ""

echo "Node workspace dir: $NODE_WORKSPACE_DIR"
echo "Node nextflow script path: $NODE_NF_SCRIPT_PATH"
echo "Use mets server: $USE_METS_SERVER"

echo ""
echo "Nf run command with Node placeholders: $NF_RUN_COMMAND"
NF_RUN_COMMAND="${NF_RUN_COMMAND//PH_HPC_WS_DIR/$NODE_WORKSPACE_DIR}"
NF_RUN_COMMAND="${NF_RUN_COMMAND//PH_NF_SCRIPT_PATH/$NODE_NF_SCRIPT_PATH}"
NF_RUN_COMMAND="${NF_RUN_COMMAND//PH_NODE_DIR_OCRD_MODELS/$NODE_DIR_OCRD_MODELS}"
NF_RUN_COMMAND="${NF_RUN_COMMAND//PH_CMD_WRAPPER/\'}"
NF_RUN_COMMAND="${NF_RUN_COMMAND//PH_NODE_DIR_PROCESSOR_SIFS/$NODE_DIR_PROCESSOR_SIFS}"
echo ""
echo "Nf run command without placeholders: $NF_RUN_COMMAND"
echo ""

# OCR-D core commands
CMD_APPTAINER_WRAPPER="apptainer exec --bind $NODE_WORKSPACE_DIR:/ws_data $PATH_SIF_OCRD_CORE"
CMD_PRINT_OCRD_VERSION="$CMD_APPTAINER_WRAPPER ocrd --version"
CMD_START_METS_SERVER="$CMD_APPTAINER_WRAPPER ocrd workspace -d /ws_data -U /ws_data/mets_server.sock server start > $NODE_WORKSPACE_DIR/mets_server.log 2>&1 &"
CMD_STOP_METS_SERVER="$CMD_APPTAINER_WRAPPER ocrd workspace -d /ws_data -U /ws_data/mets_server.sock server stop"
CMD_LIST_FILE_GROUPS="$CMD_APPTAINER_WRAPPER ocrd workspace -d /ws_data list-group"
CMD_REMOVE_FILE_GROUP="$CMD_APPTAINER_WRAPPER ocrd workspace -d /ws_data remove-group -r -f PH_FILE_GROUP > $NODE_WORKSPACE_DIR/remove_file_groups.log 2>&1"

check_existence_of_dir_scratch_base(){
  if [ ! -d "${SCRATCH_BASE}" ]; then
    echo "Creating non-existing SCRATCH_BASE folder"
    mkdir -p "${SCRATCH_BASE}"
  fi
  if [ ! -d "${SCRATCH_BASE}" ]; then
    echo "Required scratch base dir was not found: ${SCRATCH_BASE}"
    exit 1
  fi
  echo "Scratch base found/created at: ${SCRATCH_BASE}"
}

check_existence_of_dir_ocrd_models(){
  # Models directory must be previously filled with OCR-D models
  if [ ! -d "${PROJECT_DIR_OCRD_MODELS}" ]; then
    echo "Ocrd models directory not found at: ${PROJECT_DIR_OCRD_MODELS}"
    exit 1
  fi
  echo "Ocrd models directory found at: ${PROJECT_DIR_OCRD_MODELS}"
}

check_existence_of_ocrd_processor_images_to_be_used(){
  for ocrd_image in "${ocrd_processor_images[@]}"
  do
    image_path="${PROJECT_DIR_PROCESSOR_SIFS}/${ocrd_image}"
    if [ ! -f "$image_path" ]; then
      echo "Expected ocrd processor image not found at: $image_path"
      exit 1
    fi
  done
}

check_existence_of_paths() {
  check_existence_of_dir_scratch_base
  check_existence_of_dir_ocrd_models
  check_existence_of_ocrd_processor_images_to_be_used
}

clear_data_from_computing_node() {
  echo ""
  echo "Removing the OCR-D models directory from the computing node, path: ${NODE_DIR_OCRD_MODELS}"
  rm -rf "${NODE_DIR_OCRD_MODELS}"
  echo "Removing the OCR-D processor images (SIF) directory from the computing node, path: ${NODE_DIR_PROCESSOR_SIFS}"
  rm -rf "${NODE_DIR_PROCESSOR_SIFS}"
}

transfer_to_node_storage_workflow_job_zip(){
  if [ ! -f "$WORKFLOW_JOB_ZIP" ]; then
    echo "Required scratch slurm workspace zip is not available: $WORKFLOW_JOB_ZIP"
    exit 1
  fi
  echo "Transferring workflow job zip from $WORKFLOW_JOB_ZIP to $NODE_WORKFLOW_JOB_ZIP"
  cp "$WORKFLOW_JOB_ZIP" "$NODE_WORKFLOW_JOB_ZIP"
  if [ ! -f "$NODE_WORKFLOW_JOB_ZIP" ]; then
    echo "Workflow job zip not found at node local storage: $NODE_WORKFLOW_JOB_ZIP"
    clear_data_from_computing_node
    exit 1
  else
    echo "Successfully transferred workflow job zip to node local storage: $NODE_WORKFLOW_JOB_ZIP"
  fi
  echo "Removing zip: $WORKFLOW_JOB_ZIP"
  rm -f "$WORKFLOW_JOB_ZIP"
}

transfer_to_node_storage_processor_models(){
  cp -R "${PROJECT_DIR_OCRD_MODELS}" "${NODE_DIR_OCRD_MODELS}"
  if [ ! -d "${NODE_DIR_OCRD_MODELS}" ]; then
    echo "Ocrd models directory not found at node local storage: ${NODE_DIR_OCRD_MODELS}"
    clear_data_from_computing_node
    exit 1
  else
    echo "Successfully transferred ocrd models to node local storage: ${NODE_DIR_OCRD_MODELS}"
  fi
}

transfer_to_node_storage_processor_images(){
  if [ ! -d "${NODE_DIR_PROCESSOR_SIFS}" ]; then
    echo "Creating non-existing processor sif images dir: $NODE_DIR_PROCESSOR_SIFS"
    mkdir -p "${NODE_DIR_PROCESSOR_SIFS}"
  fi
  if [ ! -d "${NODE_DIR_PROCESSOR_SIFS}" ]; then
    echo "Required node processor sif images dir was not found: ${NODE_DIR_PROCESSOR_SIFS}"
    exit 1
  fi

  for ocrd_image in "${ocrd_processor_images[@]}"
  do
    ocrd_image_path="${PROJECT_DIR_PROCESSOR_SIFS}/${ocrd_image}"
    node_ocrd_image_path="${NODE_DIR_PROCESSOR_SIFS}/${ocrd_image}"
    if [ ! -f "$ocrd_image_path" ]; then
      echo "Expected ocrd processor image not found at: $ocrd_image_path"
      exit 1
    else
      echo "Transferring ocrd processor image to the compute node: ${ocrd_image}"
      cp "${ocrd_image_path}" "${node_ocrd_image_path}"
      echo "Ocrd processor image was transferred to: ${node_ocrd_image_path}"
      if [ ! -f "${node_ocrd_image_path}" ]; then
        echo "Expected ocrd processor image was copied but not found locally at: ${node_ocrd_image_path}"
        exit 1
      fi
    fi
  done
  echo ""
  eval "$CMD_PRINT_OCRD_VERSION"
  echo ""
}

unzip_workflow_job_dir_in_node() {
  if [ ! -f "$NODE_WORKFLOW_JOB_ZIP" ]; then
    echo "Required workflow job zip is not available for unzipping: $NODE_WORKFLOW_JOB_ZIP"
    exit 1
  fi

  echo "Unzipping $NODE_WORKFLOW_JOB_ZIP to: $NODE_WORKFLOW_JOB_DIR"
  unzip "$NODE_WORKFLOW_JOB_ZIP" -d "$NODE_DIR_BASE" > "$NODE_DIR_BASE/${WORKSPACE_ID}_unzipping.log"
  echo "Removing zip: $NODE_WORKFLOW_JOB_ZIP"
  mv "$NODE_DIR_BASE/${WORKSPACE_ID}_unzipping.log" "$NODE_WORKFLOW_JOB_DIR/workflow_job_unzipping.log"
  rm -f "$NODE_WORKFLOW_JOB_ZIP"

  if [ ! -d "$NODE_WORKFLOW_JOB_DIR" ]; then
    echo "Required scratch slurm workflow dir not available: $NODE_WORKFLOW_JOB_DIR"
    exit 1
  fi

  cd "$NODE_WORKFLOW_JOB_DIR" || exit 1
}

start_mets_server() {
  if [ "$USE_METS_SERVER" == "true" ] ; then
    echo "Starting the mets server for the specific workspace in the background"
    eval "$CMD_START_METS_SERVER"
    sleep 10
  fi
}

stop_mets_server() {
  if [ "$USE_METS_SERVER" == "true" ] ; then
    echo "Stopping the mets server"
    eval "$CMD_STOP_METS_SERVER"
  fi
}

execute_nextflow_workflow() {
  if [ "$USE_METS_SERVER" == "true" ] ; then
    echo "Executing the nextflow workflow with mets server"
  else
    echo "Executing the nextflow workflow without mets server"
  fi
  eval "$NF_RUN_COMMAND"

  case $? in
    0) echo "The nextflow workflow execution has finished successfully" ;;
    *) echo "The nextflow workflow execution has failed" >&2 clear_data_from_computing_node exit 1 ;;
  esac
}

list_file_groups_from_workspace() {
    all_file_groups=()
    mapfile -t all_file_groups < <($CMD_LIST_FILE_GROUPS)
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
  CMD_REMOVE_FILE_GROUP="${CMD_REMOVE_FILE_GROUP//PH_FILE_GROUP/$1}"
  eval "$CMD_REMOVE_FILE_GROUP"
  # Set the placeholder again for future invocations
  CMD_REMOVE_FILE_GROUP="${CMD_REMOVE_FILE_GROUP//$1/PH_FILE_GROUP}"
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
  find "$NODE_WORKFLOW_JOB_DIR" -type l -delete
  # Create a zip of the ocrd workspace dir
  cd "$NODE_WORKSPACE_DIR" && zip -r "$WORKSPACE_ID.zip" "." -x "*.sock" > "workspace_zipping.log"
  # Create a zip of the Nextflow run results by excluding the ocrd workspace dir
  cd "$NODE_WORKFLOW_JOB_DIR" && zip -r "$NODE_WORKFLOW_JOB_ZIP" "." -x "$WORKSPACE_ID**" > "workflow_job_zipping.log"

  case $? in
    0) echo "The results have been zipped successfully" ;;
    *) echo "The zipping of results has failed" >&2 clear_data_from_computing_node exit 1 ;;
  esac
}

transfer_from_node_storage_result_zips(){
  if [ -f "$NODE_DIR_BASE/$WORKFLOW_JOB_ID.zip" ]; then
    echo "Transferring $NODE_DIR_BASE/$WORKFLOW_JOB_ID.zip to $SCRATCH_BASE/$WORKFLOW_JOB_ID/wf_$WORKFLOW_JOB_ID.zip"
    cp "$NODE_DIR_BASE/$WORKFLOW_JOB_ID.zip" "$SCRATCH_BASE/$WORKFLOW_JOB_ID/wf_$WORKFLOW_JOB_ID.zip"
  fi
  if [ -f "$NODE_DIR_BASE/$WORKFLOW_JOB_ID/$WORKSPACE_ID.zip" ]; then
    echo "Transferring $NODE_DIR_BASE/$WORKFLOW_JOB_ID/$WORKSPACE_ID.zip to $SCRATCH_BASE/$WORKFLOW_JOB_ID/ws_$WORKSPACE_ID.zip"
    cp "$NODE_DIR_BASE/$WORKFLOW_JOB_ID/$WORKSPACE_ID.zip" "$SCRATCH_BASE/$WORKFLOW_JOB_ID/ws_$WORKSPACE_ID.zip"
  fi
}


# Main loop for workflow job execution
check_existence_of_paths
echo ""
transfer_to_node_storage_workflow_job_zip
unzip_workflow_job_dir_in_node
transfer_to_node_storage_processor_models
transfer_to_node_storage_processor_images
start_mets_server
execute_nextflow_workflow
stop_mets_server
remove_file_groups_from_workspace "$FILE_GROUPS_TO_REMOVE"
zip_results
transfer_from_node_storage_result_zips
clear_data_from_computing_node
