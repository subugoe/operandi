from logging import getLogger
from os import environ, listdir, makedirs, remove, symlink
from os.path import dirname, join, isdir, split
from pathlib import Path
from shutil import rmtree, copytree
from stat import S_ISDIR
from tempfile import mkdtemp
from time import sleep
from typing import Tuple

from operandi_utils import make_zip_archive, unpack_zip_archive
from .nhr_connector import NHRConnector

class NHRTransfer(NHRConnector):
    def __init__(self) -> None:
        logger = getLogger(name=self.__class__.__name__)
        super().__init__(logger)
        self._sftp_client = None
        self._sftp_reconnect_tries = 5
        self._sftp_reconnect_tries_remaining = self._sftp_reconnect_tries

    @property
    def sftp_client(self):
        if self._sftp_client:
            self._sftp_client.close()
            self._ssh_client = None
        self._sftp_client = self.ssh_client.open_sftp()
        # self._sftp_client.get_channel().get_transport().set_keepalive(30)

        """
        try:
            # Note: This extra check is required against aggressive
            # Firewalls that ignore the keepalive option!
            self._sftp_client.get_channel().get_transport().send_ignore()
            self._sftp_reconnect_tries_remaining = self._sftp_reconnect_tries
        except Exception as error:
            self.logger.warning(f"SFTP client failed to send ignore, connection is broken: {error}")
            if self._sftp_client:
                self._sftp_client.close()
                self._sftp_client = None
            if self._sftp_reconnect_tries_remaining < 0:
                raise Exception(f"Failed to reconnect {self._sftp_reconnect_tries} times: {error}")
            self.logger.info(f"Reconnecting the SFTP client, try times: {self._sftp_reconnect_tries_remaining}")
            self._sftp_reconnect_tries_remaining -= 1
            return self.sftp_client  # recursive call to itself to try again
        return self._sftp_client
        """

        return self._ssh_client

    def create_slurm_workspace_zip(
        self, ocrd_workspace_dir: str, workflow_job_id: str, nextflow_script_path: str,
        tempdir_prefix: str = "slurm_workspace-"
    ) -> str:
        self.logger.info(f"Entering pack_slurm_workspace")
        self.logger.info(f"ocrd_workspace_dir: {ocrd_workspace_dir}")
        self.logger.info(f"workflow_job_id: {workflow_job_id}")
        self.logger.info(f"nextflow_script_path: {nextflow_script_path}")
        self.logger.info(f"tempdir_prefix: {tempdir_prefix}")

        # Parse the nextflow file name from the script path
        nextflow_filename = nextflow_script_path.split('/')[-1]
        self.logger.info(f"Nextflow file name to be used: {nextflow_filename}")
        # Parse the ocrd workspace id from the dir path
        ocrd_workspace_id = ocrd_workspace_dir.split('/')[-1]
        self.logger.info(f"OCR-D workspace id to be used: {ocrd_workspace_id}")

        tempdir = mkdtemp(prefix=tempdir_prefix)
        self.logger.info(f"Created a temp dir name: {tempdir}")
        temp_workflow_job_dir = join(tempdir, workflow_job_id)
        makedirs(temp_workflow_job_dir)
        self.logger.info(f"Created a slurm workspace dir: {temp_workflow_job_dir}")

        dst_script_path = join(temp_workflow_job_dir, nextflow_filename)
        symlink(src=nextflow_script_path, dst=dst_script_path)
        self.logger.info(f"Symlink created from src: {nextflow_script_path}, to dst: {dst_script_path}")

        dst_workspace_path = join(temp_workflow_job_dir, ocrd_workspace_id)
        copytree(src=ocrd_workspace_dir, dst=dst_workspace_path)
        self.logger.info(f"Copied tree from src: {ocrd_workspace_dir}, to dst: {dst_workspace_path}")

        dst_zip_path = f"{temp_workflow_job_dir}.zip"
        make_zip_archive(source=temp_workflow_job_dir, destination=dst_zip_path)
        self.logger.info(f"Zip archive created from src: {temp_workflow_job_dir}, to dst: {dst_zip_path}")
        return dst_zip_path

    def put_slurm_workspace(self, local_src_slurm_zip: str, workflow_job_id: str) -> str:
        self.logger.info(f"Workflow job id to be used: {workflow_job_id}")
        hpc_dst_slurm_zip = join(self.slurm_workspaces_dir, f"{workflow_job_id}.zip")
        self.put_file(local_src=local_src_slurm_zip, remote_dst=hpc_dst_slurm_zip)
        self.logger.info(f"Put file from local src: {local_src_slurm_zip}, to remote dst: {hpc_dst_slurm_zip}")
        self.logger.info(f"Leaving put_slurm_workspace, returning: {hpc_dst_slurm_zip}")
        # Zip path inside the HPC environment
        return hpc_dst_slurm_zip

    def pack_and_put_slurm_workspace(
        self, ocrd_workspace_dir: str, workflow_job_id: str, nextflow_script_path: str,
        tempdir_prefix: str = "slurm_workspace-"
    ) -> Tuple[str, str]:
        self.logger.info(f"Entering put_slurm_workspace")
        self.logger.info(f"ocrd_workspace_dir: {ocrd_workspace_dir}")
        self.logger.info(f"workflow_job_id: {workflow_job_id}")
        self.logger.info(f"nextflow_script_path: {nextflow_script_path}")
        self.logger.info(f"tempdir_prefix: {tempdir_prefix}")

        local_src_slurm_zip = self.create_slurm_workspace_zip(
            ocrd_workspace_dir=ocrd_workspace_dir, workflow_job_id=workflow_job_id,
            nextflow_script_path=nextflow_script_path, tempdir_prefix=tempdir_prefix)
        self.logger.info(f"Created slurm workspace zip: {local_src_slurm_zip}")

        hpc_dst = self.put_slurm_workspace(local_src_slurm_zip=local_src_slurm_zip, workflow_job_id=workflow_job_id)
        self.logger.info(f"Leaving pack_and_put_slurm_workspace")
        Path(local_src_slurm_zip).unlink(missing_ok=True)
        return local_src_slurm_zip, hpc_dst

    def get_and_unpack_slurm_workspace(self, ocrd_workspace_dir: str, workflow_job_dir: str):
        self.logger.info(f"Entering get_and_unpack_slurm_workspace")
        self.logger.info(f"ocrd_workspace_dir: {ocrd_workspace_dir}")
        self.logger.info(f"workflow_job_dir: {workflow_job_dir}")

        # Parse the ocrd workspace id from the dir path
        ocrd_workspace_id = ocrd_workspace_dir.split('/')[-1]
        self.logger.info(f"OCR-D workspace id to be used: {ocrd_workspace_id}")
        workflow_job_id = workflow_job_dir.split('/')[-1]
        self.logger.info(f"Workflow job id to be used: {workflow_job_id}")

        get_src = join(self.slurm_workspaces_dir, workflow_job_id, f"{workflow_job_id}.zip")
        get_dst = join(Path(workflow_job_dir).parent.absolute(), f"{workflow_job_id}.zip")

        self._get_file_with_retries(remote_src=get_src, local_dst=get_dst)
        self.logger.info(f"Got workflow job zip file from src: {get_src}, to dst: {get_dst}")

        unpack_src = get_dst
        unpack_dst = workflow_job_dir
        try:
            unpack_zip_archive(source=unpack_src, destination=unpack_dst)
        except Exception as error:
            raise Exception(
                f"Error when unpacking workflow job zip: {error}, unpack_src: {unpack_src}, unpack_dst: {unpack_dst}")
        self.logger.info(f"Unpacked workflow job zip from src: {unpack_src}, to dst: {unpack_dst}")

        # Remove the temporary workflow job zip
        Path(unpack_src).unlink(missing_ok=True)
        self.logger.info(f"Removed the temp workflow job zip: {unpack_src}")

        # Remove the workspace dir from the local storage,
        # before transferring the results to avoid potential
        # overwrite errors or duplications
        rmtree(ocrd_workspace_dir, ignore_errors=True)
        self.logger.info(f"Removed tree dirs: {ocrd_workspace_dir}")

        get_src = join(self.slurm_workspaces_dir, workflow_job_id, ocrd_workspace_id, f"{ocrd_workspace_id}.zip")
        get_dst = join(Path(ocrd_workspace_dir).parent.absolute(), f"{ocrd_workspace_id}.zip")
        self._get_file_with_retries(remote_src=get_src, local_dst=get_dst)
        self.logger.info(f"Got workspace zip file from src: {get_src}, to dst: {get_dst}")

        unpack_src = join(Path(ocrd_workspace_dir).parent.absolute(), f"{ocrd_workspace_id}.zip")
        unpack_dst = ocrd_workspace_dir
        try:
            unpack_zip_archive(source=unpack_src, destination=unpack_dst)
        except Exception as error:
            raise Exception(
                f"Error when unpacking workspace zip: {error}, unpack_src: {unpack_src}, unpack_dst: {unpack_dst}")
        self.logger.info(f"Unpacked workspace zip from src: {unpack_src}, to dst: {unpack_dst}")

        # Remove the temporary workspace zip
        Path(unpack_src).unlink(missing_ok=True)
        self.logger.info(f"Removed the temp workspace zip: {unpack_src}")

        # Remove the workspace dir from the local workflow job dir,
        # and. Then create a symlink of the workspace dir inside the
        # workflow job dir
        workspace_dir_in_workflow_job = join(workflow_job_dir, ocrd_workspace_id)
        try:
            symlink(src=ocrd_workspace_dir, dst=workspace_dir_in_workflow_job, target_is_directory=True)
        except Exception as error:
            raise Exception(
                f"Error when symlink: {error}, src: {ocrd_workspace_dir}, dst: {workspace_dir_in_workflow_job}")
        self.logger.info(f"Symlinked from src: {ocrd_workspace_dir}, to dst: {workspace_dir_in_workflow_job}")
        self.logger.info(f"Leaving get_and_unpack_slurm_workspace")

    def _get_file_with_retries(self, remote_src, local_dst, try_times: int = 100, sleep_time: int = 3):
        if try_times < 0 or sleep_time < 0:
            raise ValueError("Negative value passed as a parameter for time")
        tries = try_times
        while tries > 0:
            try:
                self.get_file(remote_src=remote_src, local_dst=local_dst)
                break
            except Exception as error:
                tries -= 1
                if tries <= 0:
                    raise Exception(f"Error getting zip file: {error}, remote_src:{remote_src}, local_dst:{local_dst}")
                sleep(sleep_time)
                continue

    def mkdir_p(self, remote_path, mode=0o766):
        if remote_path == '/':
            self.sftp_client.chdir('/')  # absolute path so change directory to root
            return False
        if remote_path == '':
            return False  # top-level relative directory must exist
        try:
            self.sftp_client.chdir(remote_path)  # subdirectory exists
        except IOError as error:
            dir_name, base_name = split(remote_path.rstrip('/'))
            self.mkdir_p(dir_name)  # make parent directories
            self.sftp_client.mkdir(path=base_name, mode=mode)  # subdirectory missing, so created it
            self.sftp_client.chdir(base_name)
            return True

    def get_file(self, remote_src, local_dst):
        makedirs(name=Path(local_dst).parent.absolute(), exist_ok=True)
        self.sftp_client.get(remotepath=remote_src, localpath=local_dst)

    def get_dir(self, remote_src, local_dst, mode=0o766):
        """
        Downloads the contents of the remote source directory to the local destination directory.
        The remote source directory needs to exist.
        All subdirectories in source are created under destination.
        """
        makedirs(name=local_dst, mode=mode, exist_ok=True)
        for item in self.sftp_client.listdir(remote_src):
            item_src = join(remote_src, item)
            item_dst = join(local_dst, item)
            if S_ISDIR(self.sftp_client.lstat(item_src).st_mode):
                self.get_dir(remote_src=item_src, local_dst=item_dst, mode=mode)
            else:
                self.get_file(remote_src=item_src, local_dst=item_dst)

    def put_file(self, local_src, remote_dst):
        self.mkdir_p(remote_path=str(Path(remote_dst).parent.absolute()))
        self.sftp_client.put(localpath=local_src, remotepath=remote_dst)

    def put_dir(self, local_src, remote_dst, mode=0o766):
        """
        Uploads the contents of the local source directory to the remote destination directory.
        The remote destination directory needs to exist.
        All subdirectories in source are created under destination.
        """
        self.mkdir_p(remote_path=remote_dst, mode=mode)
        for item in listdir(local_src):
            item_src = join(local_src, item)
            item_dst = join(remote_dst, item)
            if isdir(item_src):
                self.put_dir(local_src=item_src, remote_dst=item_dst, mode=mode)
            else:
                self.sftp_client.chdir(remote_dst)
                self.put_file(local_src=item_src, remote_dst=item_dst)
