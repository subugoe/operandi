from typing import List
from operandi_utils.constants import OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE

# Just some placeholders to be replaced with actual paths that are
# dynamically allocated inside the node that runs the HPC slurm job
PH_NODE_DIR_OCRD_MODELS = "PH_NODE_DIR_OCRD_MODELS"
PH_NODE_DIR_PROCESSOR_SIFS = "PH_NODE_DIR_PROCESSOR_SIFS"
PH_CMD_WRAPPER = "PH_CMD_WRAPPER"


def cmd_core_print_version(hpc_ws_dir: str, ph_sif_core: str) -> str:
    return f"apptainer exec --bind {hpc_ws_dir}:/ws_data {ph_sif_core} ocrd --version"

def cmd_core_start_mets_server(hpc_ws_dir: str, ph_sif_core: str) -> str:
    command = f"apptainer exec --bind {hpc_ws_dir}:/ws_data {ph_sif_core}"
    command += f" ocrd workspace -d /ws_data -U /ws_data/mets_server.sock server start"
    command += f" > {hpc_ws_dir}/mets_server.log 2>&1 &"
    return command

def cmd_core_stop_mets_server(hpc_ws_dir: str, ph_sif_core: str) -> str:
    command = f"apptainer exec --bind {hpc_ws_dir}:/ws_data {ph_sif_core}"
    command += " ocrd workspace -d /ws_data -U /ws_data/mets_server.sock server stop"
    return command

def cmd_core_list_file_groups(hpc_ws_dir: str, ph_sif_core: str) -> str:
    command = f"apptainer exec --bind {hpc_ws_dir}:/ws_data {ph_sif_core}"
    command += " ocrd workspace -d /ws_data list-group"
    return command

def cmd_core_remove_file_group(hpc_ws_dir: str, ph_sif_core: str) -> str:
    command = f"apptainer exec --bind {hpc_ws_dir}:/ws_data {ph_sif_core}"
    command += " ocrd workspace -d /ws_data remove-group -r -f FILE_GROUP_PLACEHOLDER"
    command += f" > {hpc_ws_dir}/remove_file_groups.log 2>&1"
    return command

def cmd_nextflow_run(
    hpc_nf_script_path: str, hpc_ws_dir: str, bind_ocrd_models: str, sif_core: str, sif_ocrd_all: str,
    input_file_grp: str, mets_basename: str, use_mets_server: bool, nf_executable_steps: List[str],
    ws_pages_amount: int, cpus: int, ram: int, forks: int, use_slim_images: bool
) -> str:
    nf_run_command = f"nextflow run {hpc_nf_script_path} -ansi-log false -with-report -with-trace"
    nf_run_command += f" --input_file_group {input_file_grp}"
    nf_run_command += f" --mets_path /ws_data/{mets_basename}"
    if use_mets_server:
        nf_run_command += f" --mets_socket_path /ws_data/mets_server.sock"
    nf_run_command += f" --workspace_dir /ws_data"
    nf_run_command += f" --pages {ws_pages_amount}"

    sif_images = [OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE[exe] for exe in nf_executable_steps]
    apptainer_cmd = f"apptainer exec --bind {hpc_ws_dir}:/ws_data --bind {bind_ocrd_models}"
    # Mets caching is disabled for the core, to avoid the cache error
    # when mergin mets files https://github.com/OCR-D/core/issues/1297
    apptainer_cmd_core = f"{apptainer_cmd} --env OCRD_METS_CACHING=false"
    apptainer_cmd_step = f"{apptainer_cmd} --env OCRD_METS_CACHING=true"
    apptainer_image = sif_core if use_slim_images else sif_ocrd_all
    core_command = f"{apptainer_cmd_core} {PH_NODE_DIR_PROCESSOR_SIFS}/{apptainer_image}"
    nf_run_command += f" --env_wrapper_cmd_core {PH_CMD_WRAPPER}{core_command}{PH_CMD_WRAPPER}"

    index = 0
    for sif_image in sif_images:
        apptainer_image = sif_image if use_slim_images else sif_ocrd_all
        step_command = f"{apptainer_cmd_step} {PH_NODE_DIR_PROCESSOR_SIFS}/{apptainer_image}"
        nf_run_command += f" --env_wrapper_cmd_step{index} {PH_CMD_WRAPPER}{step_command}{PH_CMD_WRAPPER}"
        index += 1
    nf_run_command += f" --cpus {cpus}"
    nf_run_command += f" --ram {ram}"
    nf_run_command += f" --forks {forks}"
    return nf_run_command
