from logging import getLogger
from os import listdir, makedirs, symlink
from os.path import isdir, split
from pathlib import Path
from shutil import rmtree, copytree
from stat import S_ISDIR
from tempfile import mkdtemp
from time import sleep
from typing import Tuple

from operandi_utils import make_zip_archive, unpack_zip_archive
from .nhr_connector import NHRConnector

SFTP_RECONNECT_TRIES = 5
DOWNLOAD_FILE_TRY_TIMES = 100
DOWNLOAD_FILE_SLEEP_TIME = 3

class NHRTransfer(NHRConnector):
    def __init__(self) -> None:
        logger = getLogger(name=self.__class__.__name__)
        super().__init__(logger)
        self._operandi_data_root = ""
        self._sftp_client = None
        self._sftp_reconnect_tries = SFTP_RECONNECT_TRIES
        self._sftp_reconnect_tries_remaining = self._sftp_reconnect_tries
        _ = self.sftp_client  # forces a connection

    @property
    def sftp_client(self):
        if self._sftp_client:
            self._sftp_client.close()
            self._ssh_client = None
        self._sftp_client = self.ssh_client.open_sftp()
        return self._sftp_client

    def create_slurm_workspace_zip(
        self, ocrd_workspace_dir: Path, workflow_job_id: str, nextflow_script_path: Path,
        tempdir_prefix: str = "slurm_workspace-"
    ) -> Path:
        self.logger.info(f"Entering pack_slurm_workspace")
        self.logger.info(f"ocrd_workspace_dir: {ocrd_workspace_dir}")
        self.logger.info(f"workflow_job_id: {workflow_job_id}")
        self.logger.info(f"nextflow_script_path: {nextflow_script_path}")
        self.logger.info(f"tempdir_prefix: {tempdir_prefix}")

        # Parse the nextflow file name from the script path
        nextflow_filename = nextflow_script_path.name
        self.logger.info(f"Nextflow file name to be used: {nextflow_filename}")
        # Parse the ocrd workspace id from the dir path
        ocrd_workspace_id = ocrd_workspace_dir.name
        self.logger.info(f"OCR-D workspace id to be used: {ocrd_workspace_id}")

        tempdir = mkdtemp(prefix=tempdir_prefix)
        self.logger.info(f"Created a temp dir name: {tempdir}")
        temp_workflow_job_dir = Path(tempdir, workflow_job_id)
        makedirs(temp_workflow_job_dir)
        self.logger.info(f"Created a slurm workspace dir: {temp_workflow_job_dir}")

        dst_script_path = Path(temp_workflow_job_dir, nextflow_filename)
        symlink(src=nextflow_script_path, dst=dst_script_path)
        self.logger.info(f"Symlink created from src: {nextflow_script_path}, to dst: {dst_script_path}")

        dst_workspace_path = Path(temp_workflow_job_dir, ocrd_workspace_id)
        copytree(src=ocrd_workspace_dir, dst=dst_workspace_path)
        self.logger.info(f"Copied tree from src: {ocrd_workspace_dir}, to dst: {dst_workspace_path}")

        dst_zip_path = Path(f"{temp_workflow_job_dir}.zip")
        make_zip_archive(source=temp_workflow_job_dir, destination=dst_zip_path)
        self.logger.info(f"Zip archive created from src: {temp_workflow_job_dir}, to dst: {dst_zip_path}")
        return dst_zip_path

    def put_slurm_workspace(self, local_src_slurm_zip: Path, workflow_job_id: str) -> Path:
        self.logger.info(f"Workflow job id to be used: {workflow_job_id}")
        hpc_dst_slurm_zip = Path(self.slurm_workspaces_dir, f"{workflow_job_id}.zip")
        _ = self.sftp_client  # Force reconnect of the SFTP Client
        self.put_file(local_src=local_src_slurm_zip, remote_dst=hpc_dst_slurm_zip)
        self.logger.info(f"Put file from local src: {local_src_slurm_zip}, to remote dst: {hpc_dst_slurm_zip}")
        self.logger.info(f"Leaving put_slurm_workspace, returning: {hpc_dst_slurm_zip}")
        # Zip path inside the HPC environment
        return hpc_dst_slurm_zip

    def pack_and_put_slurm_workspace(
        self, ocrd_workspace_dir: Path, workflow_job_id: str, nextflow_script_path: Path,
        tempdir_prefix: str = "slurm_workspace-"
    ) -> Tuple[Path, Path]:
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

    def _download_file_with_retries(
        self, remote_src, local_dst, try_times: int = DOWNLOAD_FILE_TRY_TIMES,
        sleep_time: int = DOWNLOAD_FILE_SLEEP_TIME
    ):
        if try_times < 0 or sleep_time < 0:
            self.logger.warning("Negative value passed as a parameter to any of the time options, using defaults.")
            try_times = DOWNLOAD_FILE_TRY_TIMES
            sleep_time = DOWNLOAD_FILE_SLEEP_TIME
        tries = try_times
        while tries > 0:
            try:
                self.get_file(remote_src=str(remote_src), local_dst=str(local_dst))
                break
            except Exception as error:
                tries -= 1
                if tries <= 0:
                    raise Exception(f"Error getting zip file: {error}, remote_src:{remote_src}, local_dst:{local_dst}")
                sleep(sleep_time)
                continue

    def download_slurm_job_log_file(self, slurm_job_id: str, local_wf_job_dir: Path) -> Path:
        workflow_job_id = Path(local_wf_job_dir).name
        get_src = Path(self.slurm_workspaces_dir, workflow_job_id, f"slurm-job-{slurm_job_id}.txt")
        get_dst = Path(local_wf_job_dir, f"slurm-job-{slurm_job_id}.txt")
        self.logger.info(f"Downloading slurm job log from HPC source: {get_src}")
        self.logger.info(f"Downloading slurm job log to local destination: {get_dst}")
        self._download_file_with_retries(remote_src=get_src, local_dst=get_dst)
        self.logger.info(f"Successfully downloaded slurm job log to: {get_dst}")
        return get_dst

    def _download_workflow_job_zip(self, local_wf_job_dir: Path) -> Path:
        workflow_job_id = Path(local_wf_job_dir).name
        get_src = Path(self.slurm_workspaces_dir, workflow_job_id, f"{workflow_job_id}.zip")
        get_dst = Path(local_wf_job_dir.parent.absolute(), f"{workflow_job_id}.zip")
        self.logger.info(f"Downloading workflow job zip from HPC source: {get_src}")
        self.logger.info(f"Downloading workflow job zip to local destination: {get_dst}")
        self._download_file_with_retries(remote_src=get_src, local_dst=get_dst)
        self.logger.info(f"Successfully downloaded zip of workflow job id: {workflow_job_id}")
        return get_dst

    def _unzip_workflow_job_dir(self, local_wf_job_zip: Path, local_wf_job_dir: Path, remove_zip: bool = True) -> Path:
        unpack_src = local_wf_job_zip
        unpack_dst = local_wf_job_dir
        self.logger.info(f"Unzipping source workflow job zip path: {unpack_src}")
        self.logger.info(f"Unzipping workflow job zip to destination: {unpack_dst}")
        try:
            unpack_zip_archive(source=unpack_src, destination=unpack_dst)
        except Exception as error:
            if remove_zip:
                Path(unpack_src).unlink(missing_ok=True)
                self.logger.info(f"Removed the temp workflow job zip: {unpack_src}")
            raise Exception(
                f"Error when unpacking workflow job zip: {error}, unpack_src: {unpack_src}, unpack_dst: {unpack_dst}")
        self.logger.info(f"Unpacked workflow job zip from src: {unpack_src}, to dst: {unpack_dst}")
        if remove_zip:
            Path(unpack_src).unlink(missing_ok=True)
            self.logger.info(f"Removed the temp workflow job zip: {unpack_src}")
        return unpack_dst

    def _download_workspace_zip(self, local_ocrd_ws_dir: Path, local_wf_job_dir: Path) -> Path:
        workflow_job_id = Path(local_wf_job_dir).name
        workspace_id = Path(local_ocrd_ws_dir).name
        get_src = Path(self.slurm_workspaces_dir, workflow_job_id, workspace_id, f"{workspace_id}.zip")
        get_dst = Path(local_ocrd_ws_dir.parent.absolute(), f"{workspace_id}.zip")
        self.logger.info(f"Downloading workspace zip from HPC source: {get_src}")
        self.logger.info(f"Downloading workspace zip to local destination: {get_dst}")
        self._download_file_with_retries(remote_src=get_src, local_dst=get_dst)
        self.logger.info(f"Successfully downloaded zip of workspace id: {workspace_id}")
        return get_dst

    def _unzip_workspace_dir(self, local_ws_dir_zip: Path, local_ocrd_ws_dir: Path, remove_zip: bool = True):
        unpack_src = local_ws_dir_zip
        unpack_dst = local_ocrd_ws_dir
        try:
            unpack_zip_archive(source=unpack_src, destination=unpack_dst)
        except Exception as error:
            if remove_zip:
                Path(unpack_src).unlink(missing_ok=True)
                self.logger.info(f"Removed the temp workspace zip: {unpack_src}")
            raise Exception(
                f"Error when unpacking workspace zip: {error}, unpack_src: {unpack_src}, unpack_dst: {unpack_dst}")
        self.logger.info(f"Unpacked workspace zip from src: {unpack_src}, to dst: {unpack_dst}")

        if remove_zip:
            Path(unpack_src).unlink(missing_ok=True)
            self.logger.info(f"Removed the temp workspace zip: {unpack_src}")

    def get_and_unpack_slurm_workspace(self, ocrd_workspace_dir: Path, workflow_job_dir: Path):
        _ = self.sftp_client  # Force reconnect of the SFTP Client
        wf_job_zip_path = self._download_workflow_job_zip(local_wf_job_dir=workflow_job_dir)
        self._unzip_workflow_job_dir(wf_job_zip_path, workflow_job_dir, True)

        # TODO: This is still not optimal. Consider to back up instead of removing before downloading.
        # Remove the workspace dir from the local storage,
        # before transferring the results to avoid potential
        # overwrite errors or duplications
        rmtree(ocrd_workspace_dir, ignore_errors=True)
        self.logger.info(f"Removed tree dirs: {ocrd_workspace_dir}")

        ws_zip_path = self._download_workspace_zip(ocrd_workspace_dir, workflow_job_dir)
        self._unzip_workspace_dir(ws_zip_path, ocrd_workspace_dir)

        # Remove the workspace dir from the local workflow job dir,
        # and then create a symlink of the workspace dir inside the
        # workflow job dir
        workspace_dir_in_workflow_job = Path(workflow_job_dir, ocrd_workspace_dir.name)
        try:
            symlink(src=ocrd_workspace_dir, dst=workspace_dir_in_workflow_job, target_is_directory=True)
        except Exception as error:
            raise Exception(
                f"Error when symlink: {error}, src: {ocrd_workspace_dir}, dst: {workspace_dir_in_workflow_job}")
        self.logger.info(f"Symlinked from src: {ocrd_workspace_dir}, to dst: {workspace_dir_in_workflow_job}")
        self.logger.info(f"Leaving get_and_unpack_slurm_workspace")

    def mkdir_p(self, remote_path, mode=0o766):
        if remote_path == '/':
            self._sftp_client.chdir('/')  # absolute path so change directory to root
            return False
        if remote_path == '':
            return False  # top-level relative directory must exist
        try:
            self._sftp_client.chdir(remote_path)  # subdirectory exists
        except IOError as error:
            dir_name, base_name = split(remote_path.rstrip('/'))
            self.mkdir_p(dir_name)  # make parent directories
            self._sftp_client.mkdir(path=base_name, mode=mode)  # subdirectory missing, so created it
            self._sftp_client.chdir(base_name)
            return True

    def get_file(self, remote_src, local_dst):
        makedirs(name=Path(local_dst).parent.absolute(), exist_ok=True)
        self._sftp_client.get(remotepath=str(remote_src), localpath=str(local_dst))

    def get_dir(self, remote_src, local_dst, mode=0o766):
        """
        Downloads the contents of the remote source directory to the local destination directory.
        The remote source directory needs to exist.
        All subdirectories in source are created under destination.
        """
        makedirs(name=local_dst, mode=mode, exist_ok=True)
        for item in self._sftp_client.listdir(str(remote_src)):
            item_src = Path(remote_src, item)
            item_dst = Path(local_dst, item)
            if S_ISDIR(self._sftp_client.lstat(str(item_src)).st_mode):
                self.get_dir(remote_src=item_src, local_dst=item_dst, mode=mode)
            else:
                self.get_file(remote_src=item_src, local_dst=item_dst)

    def put_file(self, local_src, remote_dst):
        self.mkdir_p(remote_path=str(Path(remote_dst).parent.absolute()))
        self._sftp_client.put(localpath=str(local_src), remotepath=str(remote_dst))

    def put_dir(self, local_src, remote_dst, mode=0o766):
        """
        Uploads the contents of the local source directory to the remote destination directory.
        The remote destination directory needs to exist.
        All subdirectories in source are created under destination.
        """
        self.mkdir_p(remote_path=str(remote_dst), mode=mode)
        for item in listdir(str(local_src)):
            item_src = Path(local_src, item)
            item_dst = Path(remote_dst, item)
            if isdir(item_src):
                self.put_dir(local_src=item_src, remote_dst=item_dst, mode=mode)
            else:
                self._sftp_client.chdir(str(remote_dst))
                self.put_file(local_src=item_src, remote_dst=item_dst)
