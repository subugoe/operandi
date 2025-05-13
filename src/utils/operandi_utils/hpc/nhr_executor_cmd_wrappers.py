from typing import List
from operandi_utils.constants import OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE

# Just some placeholders to be replaced with actual paths that are
# dynamically allocated inside the node that runs the HPC slurm job
PH_NODE_DIR_OCRD_MODELS = "PH_NODE_DIR_OCRD_MODELS"
PH_NODE_DIR_PROCESSOR_SIFS = "PH_NODE_DIR_PROCESSOR_SIFS"
PH_NF_SCRIPT_PATH = "PH_NF_SCRIPT_PATH"
PH_HPC_WS_DIR = "PH_HPC_WS_DIR"
PH_CMD_WRAPPER = "PH_CMD_WRAPPER"


def cmd_nextflow_run(
    sif_core: str, input_file_grp: str, mets_basename: str, use_mets_server: bool,
    nf_executable_steps: List[str], ws_pages_amount: int, cpus: int, ram: int, forks: int
) -> str:
    nf_run_command = f"nextflow run {PH_NF_SCRIPT_PATH} -ansi-log false -with-report -with-trace"
    nf_run_command += f" --input_file_group {input_file_grp}"
    nf_run_command += f" --mets_path /ws_data/{mets_basename}"
    if use_mets_server:
        nf_run_command += f" --mets_socket_path /ws_data/mets_server.sock"
    nf_run_command += f" --workspace_dir /ws_data"
    nf_run_command += f" --pages {ws_pages_amount}"

    bind_ocrd_models = f"{PH_NODE_DIR_OCRD_MODELS}/ocrd-resources:/usr/local/share/ocrd-resources"
    apptainer_cmd = f"apptainer exec --bind {PH_HPC_WS_DIR}:/ws_data --bind {bind_ocrd_models}"
    # Mets caching is disabled for the core, to avoid the cache error
    # when merging mets files https://github.com/OCR-D/core/issues/1297
    core_command = f"{apptainer_cmd} --env OCRD_METS_CACHING=false {PH_NODE_DIR_PROCESSOR_SIFS}/{sif_core}"
    nf_run_command += f" --env_wrapper_cmd_core {PH_CMD_WRAPPER}{core_command}{PH_CMD_WRAPPER}"

    index = 0
    sif_images = [OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE[exe] for exe in nf_executable_steps]
    for sif_image in sif_images:
        step_command = f"{apptainer_cmd} --env OCRD_METS_CACHING=true {PH_NODE_DIR_PROCESSOR_SIFS}/{sif_image}"
        nf_run_command += f" --env_wrapper_cmd_step{index} {PH_CMD_WRAPPER}{step_command}{PH_CMD_WRAPPER}"
        index += 1
    nf_run_command += f" --cpus {cpus}"
    nf_run_command += f" --ram {ram}"
    nf_run_command += f" --forks {forks}"
    return nf_run_command
