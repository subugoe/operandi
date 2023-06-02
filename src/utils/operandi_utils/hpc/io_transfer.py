from os import mkdir, remove, symlink
from os.path import dirname, exists, isfile, join
from pathlib import Path
import SSHLibrary
from shutil import rmtree, copytree
from tempfile import mkdtemp
from typing import Tuple

from operandi_utils import make_zip_archive, unpack_zip_archive
from .constants import (
    OPERANDI_HPC_DIR_BATCH_SCRIPTS,
    OPERANDI_HPC_DIR_SLURM_WORKSPACES,
    OPERANDI_HPC_HOST_TRANSFER,
    OPERANDI_HPC_USERNAME,
    OPERANDI_HPC_SSH_KEYPATH
)


class HPCIOTransfer:
    def __init__(
            self,
            scp="ON",
            scp_preserve_times=True,
            mode="0755"
    ):
        # TODO: Handle the exceptions properly
        self.scp = scp
        self.scp_preserve_times = scp_preserve_times
        self.mode = mode
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
        hpc_batch_script_path = join(OPERANDI_HPC_DIR_BATCH_SCRIPTS, batch_script_id)
        self._put_file(
            source=local_batch_script_path,
            destination=hpc_batch_script_path
        )
        return hpc_batch_script_path

    def pack_and_put_slurm_workspace(
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

        tempdir = mkdtemp(prefix="slurm_workspace-")
        temp_workflow_job_dir = join(join(tempdir, workflow_job_id))
        mkdir(temp_workflow_job_dir)

        symlink(
            src=nextflow_script_path,
            dst=join(temp_workflow_job_dir, nextflow_script_id),
        )
        copytree(
            src=ocrd_workspace_dir,
            dst=join(temp_workflow_job_dir, ocrd_workspace_id)
        )
        make_zip_archive(temp_workflow_job_dir, f"{temp_workflow_job_dir}.zip")
        self._put_file(
            source=f"{temp_workflow_job_dir}.zip",
            destination=join(OPERANDI_HPC_DIR_SLURM_WORKSPACES, f"{workflow_job_id}.zip")
        )

        # Zip path inside the HPC environment
        return OPERANDI_HPC_DIR_SLURM_WORKSPACES, nextflow_script_id

    def get_and_unpack_slurm_workspace(
            self,
            ocrd_workspace_id: str,
            ocrd_workspace_dir: str,
            hpc_slurm_workspace_path: str,
            workflow_job_id: str,
            workflow_job_dir: str
    ):
        get_src = join(hpc_slurm_workspace_path, workflow_job_id, f"{workflow_job_id}.zip")
        get_dst = join(Path(workflow_job_dir).parent.absolute(), f"{workflow_job_id}.zip")
        try:
            self._get_file(source=get_src, destination=get_dst)
        except Exception as error:
            raise Exception(
                f"error when getting file: {error}, get_src: {get_src}, get_dst: {get_dst}"
            )

        unpack_src = join(Path(workflow_job_dir).parent.absolute(), f"{workflow_job_id}.zip")
        unpack_dst = workflow_job_dir
        try:
            unpack_zip_archive(source=unpack_src, destination=unpack_dst)
        except Exception as error:
            raise Exception(
                f"error when unpacking zip: {error}, unpack_src: {unpack_src}, unpack_dst: {unpack_dst}"
            )

        # Remove the temporary zip
        remove(unpack_src)

        # Remove the workspace dir from the local storage,
        # before transferring the results to avoid potential
        # overwrite errors or duplications
        rmtree(ocrd_workspace_dir, ignore_errors=True)

        get_src = join(hpc_slurm_workspace_path, workflow_job_id, ocrd_workspace_id, f"{ocrd_workspace_id}.zip")
        get_dst = join(Path(ocrd_workspace_dir).parent.absolute(), f"{ocrd_workspace_id}.zip")
        try:
            self._get_file(source=get_src, destination=get_dst)
        except Exception as error:
            raise Exception(
                f"error when getting file2: {error}, get_src: {get_src}, get_dst: {get_dst}"
            )

        unpack_src = join(Path(ocrd_workspace_dir).parent.absolute(), f"{ocrd_workspace_id}.zip")
        unpack_dst = ocrd_workspace_dir
        try:
            unpack_zip_archive(source=unpack_src, destination=unpack_dst)
        except Exception as error:
            raise Exception(
                f"error when unpacking zip2: {error}, unpack_src: {unpack_src}, unpack_dst: {unpack_dst}"
            )

        # Remove the temporary zip
        remove(unpack_src)

        # Remove the workspace dir from the local workflow job dir,
        # and. Then create a symlink of the workspace dir inside the
        # workflow job dir
        workspace_dir_in_workflow_job = join(workflow_job_dir, ocrd_workspace_id)
        try:
            symlink(
                src=ocrd_workspace_dir,
                dst=workspace_dir_in_workflow_job,
                target_is_directory=True
            )
        except Exception as error:
            raise Exception(
                f"error when symlinking: {error}, src: {ocrd_workspace_dir}, dst: {workspace_dir_in_workflow_job}"
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
