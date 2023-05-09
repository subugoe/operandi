from os import symlink
from os.path import dirname, exists, isfile, join
from pathlib import Path
import SSHLibrary
from shutil import rmtree
from typing import Tuple

from .constants import (
    OPERANDI_HPC_HOST_TRANSFER,
    OPERANDI_HPC_USERNAME,
    OPERANDI_HPC_SSH_KEYPATH,
    OPERANDI_HPC_HOME_PATH
)


class HPCIOTransfer:
    def __init__(
            self,
            hpc_home_path: str = OPERANDI_HPC_HOME_PATH,
            scp="ON",
            scp_preserve_times=True,
            mode="0755"
    ):
        # TODO: Handle the exceptions properly
        self.scp = scp
        self.scp_preserve_times = scp_preserve_times
        self.mode = mode
        self.hpc_home_path = hpc_home_path
        self.__ssh_io_transfer = None

    # This connection is used only
    # for IO transfers to/from HPC cluster
    def connect(
            self,
            host=OPERANDI_HPC_HOST_TRANSFER,
            username=OPERANDI_HPC_USERNAME,
            key_path=OPERANDI_HPC_SSH_KEYPATH
    ):
        keyfile = self.__check_keyfile_existence(key_path)
        if not keyfile:
            print(f"Error: HPC key path does not exist or is not readable!")
            print(f"Checked path: \n{key_path}")
            exit(1)

        self.__ssh_io_transfer = SSHLibrary.SSHLibrary()
        self.__ssh_io_transfer.open_connection(host=host)
        self.__ssh_io_transfer.login_with_public_key(
            username=username,
            keyfile=keyfile,
            allow_agent=True
        )

    def put_batch_script(self, batch_script_id: str) -> str:
        local_batch_script_path = join(dirname(__file__), "batch_scripts", batch_script_id)
        hpc_batch_script_path = join(self.hpc_home_path, "operandi", "batch_scripts", batch_script_id)
        self._put_file(
            source=local_batch_script_path,
            destination=hpc_batch_script_path
        )
        return hpc_batch_script_path

    # The slurm workspace in the HPC contains:
    # 1) Nextflow Script
    # 2) Ocrd workspace directory "data" that has:
    #   2.1) a mets file
    #   2.2) input file group folder
    def put_slurm_workspace(
            self,
            ocrd_workspace_id: str,
            ocrd_workspace_dir: str,
            workflow_job_id: str,
            nextflow_script_path: str = None
    ) -> Tuple[str, str]:

        # The provided scripts are always renamed to:
        nextflow_script_id = "user_workflow.nf"

        # If no nextflow script is provided, then the default one is used
        if not nextflow_script_path:
            nextflow_script_id = "default_workflow.nf"
            nextflow_script_path = join(dirname(__file__), "nextflow_workflows", nextflow_script_id)

        hpc_slurm_workspace_path = join(self.hpc_home_path, "operandi", "slurm_workspaces", workflow_job_id)
        # put the nextflow script
        self._put_file(
            source=nextflow_script_path,
            destination=join(hpc_slurm_workspace_path, nextflow_script_id)
        )
        # put the ocrd workspace
        self._put_directory(
            source=ocrd_workspace_dir,
            destination=join(hpc_slurm_workspace_path, ocrd_workspace_id),
            recursive=True
        )
        return hpc_slurm_workspace_path, nextflow_script_id

    def get_slurm_workspace(
            self,
            ocrd_workspace_id: str,
            ocrd_workspace_dir: str,
            hpc_slurm_workspace_path: str,
            workflow_job_dir: str
    ):
        self._get_directory(
            source=hpc_slurm_workspace_path,
            destination=Path(workflow_job_dir).parent.absolute(),
            recursive=True
        )

        # Remove the workspace dir from the local storage,
        # before transferring the results to avoid potential
        # overwrite errors or duplications
        rmtree(ocrd_workspace_dir, ignore_errors=True)

        self._get_directory(
            source=join(hpc_slurm_workspace_path, ocrd_workspace_id),
            destination=Path(ocrd_workspace_dir).parent.absolute(),
            recursive=True
        )

        # Remove the workspace dir from the local workflow job dir,
        # and. Then create a symlink of the workspace dir inside the
        # workflow job dir
        workspace_dir_in_workflow_job = join(workflow_job_dir, ocrd_workspace_id)
        rmtree(workspace_dir_in_workflow_job)
        symlink(
            src=ocrd_workspace_dir,
            dst=workspace_dir_in_workflow_job,
            target_is_directory=True
        )

    @staticmethod
    def __check_keyfile_existence(hpc_key_path):
        if exists(hpc_key_path) and isfile(hpc_key_path):
            return hpc_key_path
        return None

    def _put_file(self, source, destination):
        self.__ssh_io_transfer.put_file(
            source=source,
            destination=destination,
            mode=self.mode,
            scp=self.scp,
            scp_preserve_times=self.scp_preserve_times
        )

    def _put_directory(self, source, destination, recursive=True):
        self.__ssh_io_transfer.put_directory(
            source=source,
            destination=destination,
            mode=self.mode,
            recursive=recursive,
            scp=self.scp,
            scp_preserve_times=self.scp_preserve_times
        )

    def _get_file(self, source, destination):
        self.__ssh_io_transfer.get_file(
            source=source,
            destination=destination,
            scp=self.scp,
            scp_preserve_times=self.scp_preserve_times
        )

    def _get_directory(self, source, destination, recursive=True):
        self.__ssh_io_transfer.get_directory(
            source=source,
            destination=destination,
            recursive=recursive,
            scp=self.scp,
            scp_preserve_times=self.scp_preserve_times
        )
