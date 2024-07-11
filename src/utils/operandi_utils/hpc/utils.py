from pathlib import Path

from .constants import (
    HPC_DIR_BATCH_SCRIPTS, HPC_DIR_SLURM_WORKSPACES, HPC_PATH_HOME_USERS, HPC_PATH_SCRATCH1_OCR_PROJECT)


def check_keyfile_existence(hpc_key_path: Path):
    if not hpc_key_path.exists():
        raise FileNotFoundError(f"HPC private key path does not exists: {hpc_key_path}")
    if not hpc_key_path.is_file():
        raise FileNotFoundError(f"HPC private key path is not a file: {hpc_key_path}")


def resolve_hpc_user_home_dir(username: str) -> str:
    return f"{HPC_PATH_HOME_USERS}/{username}"


def resolve_hpc_project_root_dir(project_root_dir: str) -> str:
    return f"{HPC_PATH_SCRATCH1_OCR_PROJECT}/{project_root_dir}"


def resolve_hpc_batch_scripts_dir(
    project_root_dir: str, batch_scripts_dir: str = HPC_DIR_BATCH_SCRIPTS
) -> str:
    return f"{resolve_hpc_project_root_dir(project_root_dir)}/{batch_scripts_dir}"


def resolve_hpc_slurm_workspaces_dir(
    project_root_dir: str, slurm_workspaces_dir: str = HPC_DIR_SLURM_WORKSPACES
) -> str:
    return f"{resolve_hpc_project_root_dir(project_root_dir)}/{slurm_workspaces_dir}"
