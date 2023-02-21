import os
import shutil

from .constants import (
    WORKSPACES_DIR
)

MODULE_PATH = os.path.dirname(__file__)


def get_nf_workspace_dir(workspace_id, local):
    if local:
        # Set location to local - ws_local
        location = "ws_local"
    else:
        # Set location to hpc - ws_hpc
        location = "ws_hpc"
    nf_workspace_dir = f"{WORKSPACES_DIR}/{location}/{workspace_id}"
    # print(f"Getting nf_workspace_dir: {nf_workspace_dir}")
    return nf_workspace_dir


def get_nf_script(workspace_id, local):
    nf_workspace_dir = get_nf_workspace_dir(workspace_id, local)
    # This is the only supported Nextflow file currently
    if local:
        script_id = "local_nextflow.nf"
    else:
        script_id = "hpc_nextflow.nf"
    nf_script_path = f"{nf_workspace_dir}/bin/{script_id}"
    # print(f"Getting nextflow_script: {nf_script_path}")
    return nf_script_path


def get_ocrd_workspace_dir(workspace_id, local):
    nf_workspace_dir = get_nf_workspace_dir(workspace_id, local)
    ocrd_workspace_dir = f"{nf_workspace_dir}/bin/ocrd-workspace"
    # print(f"Getting ocrd_workspace_dir: {ocrd_workspace_dir}")
    return ocrd_workspace_dir


def copy_batch_script(workspace_id, script_id="base_script.sh"):
    src_path = f"{MODULE_PATH}/batch_scripts/{script_id}"
    # destination is the workspace dir of workspace_id
    dst_path = get_nf_workspace_dir(workspace_id, local=False)

    if not os.path.exists(dst_path):
        os.makedirs(dst_path, exist_ok=True)

    if os.path.exists(src_path):
        shutil.copy2(src_path, dst_path)


def copy_nextflow_config(workspace_id, config_id="nextflow.config"):
    src_path = f"{MODULE_PATH}/nextflow_files/configs/{config_id}"
    workspace_dir = get_nf_workspace_dir(workspace_id, local=False)
    dst_path = f"{workspace_dir}/bin"

    if not os.path.exists(dst_path):
        os.makedirs(dst_path, exist_ok=True)

    if os.path.exists(src_path):
        shutil.copy2(src_path, dst_path)


def copy_nextflow_script(workspace_id, local):
    if local:
        nf_script_id = "local_nextflow.nf"
        workspace_dir = get_nf_workspace_dir(workspace_id, local=True)
    else:
        nf_script_id = "hpc_nextflow.nf"
        workspace_dir = get_nf_workspace_dir(workspace_id, local=False)

    src_path = f"{MODULE_PATH}/nextflow_files/scripts/{nf_script_id}"
    dst_path = f"{workspace_dir}/bin"

    if not os.path.exists(dst_path):
        os.makedirs(dst_path, exist_ok=True)

    if os.path.exists(src_path):
        shutil.copy2(src_path, dst_path)
