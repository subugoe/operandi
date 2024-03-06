from logging import getLogger
from os import environ, listdir, makedirs, remove, symlink
from os.path import dirname, join, isdir, split
from pathlib import Path
from shutil import rmtree, copytree
from stat import S_ISDIR
from tempfile import mkdtemp
from typing import List, Tuple

from operandi_utils import make_zip_archive, unpack_zip_archive
from .connector import HPCConnector
from .constants import HPC_TRANSFER_HOSTS, HPC_TRANSFER_PROXY_HOSTS


class HPCTransfer(HPCConnector):
    def __init__(
        self,
        transfer_hosts: List[str] = HPC_TRANSFER_HOSTS,
        proxy_hosts: List[str] = HPC_TRANSFER_PROXY_HOSTS,
        username: str = environ.get("OPERANDI_HPC_USERNAME", None),
        key_path: str = environ.get("OPERANDI_HPC_SSH_KEYPATH", None),
        project_name: str = environ.get("OPERANDI_HPC_PROJECT_NAME", None)
    ) -> None:
        if not username:
            raise ValueError("Environment variable not set: OPERANDI_HPC_USERNAME")
        if not key_path:
            raise ValueError("Environment variable not set: OPERANDI_HPC_SSH_KEYPATH")
        if not project_name:
            raise ValueError("Environment variable not set: OPERANDI_HPC_PROJECT_NAME")
        super().__init__(
            hpc_hosts=transfer_hosts,
            proxy_hosts=proxy_hosts,
            project_name=environ.get("OPERANDI_HPC_PROJECT_NAME", None),
            log=getLogger("operandi_utils.hpc.transfer"),
            username=username,
            key_path=Path(key_path),
            key_pass=None
        )

    def put_batch_script(self, batch_script_id: str) -> str:
        local_batch_script_path = join(dirname(__file__), "batch_scripts", batch_script_id)
        hpc_batch_script_path = join(self.batch_scripts_dir, batch_script_id)
        self.put_file(
            local_src=local_batch_script_path,
            remote_dst=hpc_batch_script_path
        )
        self.log.info(f"Put file from local src: {local_batch_script_path}, to dst: {hpc_batch_script_path}")
        return hpc_batch_script_path

    def create_slurm_workspace_zip(
        self,
        ocrd_workspace_dir: str,
        workflow_job_id: str,
        nextflow_script_path: str,
        tempdir_prefix: str = "slurm_workspace-"
    ) -> str:
        self.log.info(f"Entering pack_slurm_workspace")
        self.log.info(f"ocrd_workspace_dir: {ocrd_workspace_dir}")
        self.log.info(f"workflow_job_id: {workflow_job_id}")
        self.log.info(f"nextflow_script_path: {nextflow_script_path}")
        self.log.info(f"tempdir_prefix: {tempdir_prefix}")

        # Parse the nextflow file name from the script path
        nextflow_filename = nextflow_script_path.split('/')[-1]
        self.log.info(f"Nextflow file name to be used: {nextflow_filename}")
        # Parse the ocrd workspace id from the dir path
        ocrd_workspace_id = ocrd_workspace_dir.split('/')[-1]
        self.log.info(f"OCR-D workspace id to be used: {ocrd_workspace_id}")

        tempdir = mkdtemp(prefix=tempdir_prefix)
        self.log.info(f"Created a temp dir name: {tempdir}")
        temp_workflow_job_dir = join(tempdir, workflow_job_id)
        makedirs(temp_workflow_job_dir)
        self.log.info(f"Created a slurm workspace dir: {temp_workflow_job_dir}")

        dst_script_path = join(temp_workflow_job_dir, nextflow_filename)
        symlink(src=nextflow_script_path, dst=dst_script_path)
        self.log.info(f"Symlink created from src: {nextflow_script_path}, to dst: {dst_script_path}")

        dst_workspace_path = join(temp_workflow_job_dir, ocrd_workspace_id)
        copytree(src=ocrd_workspace_dir, dst=dst_workspace_path)
        self.log.info(f"Copied tree from src: {ocrd_workspace_dir}, to dst: {dst_workspace_path}")

        dst_zip_path = f"{temp_workflow_job_dir}.zip"
        make_zip_archive(source=temp_workflow_job_dir, destination=dst_zip_path)
        self.log.info(f"Zip archive created from src: {temp_workflow_job_dir}, to dst: {dst_zip_path}")
        return dst_zip_path

    def put_slurm_workspace(self, local_src_slurm_zip: str, workflow_job_id: str) -> str:
        self.log.info(f"Workflow job id to be used: {workflow_job_id}")
        hpc_dst_slurm_zip = join(self.slurm_workspaces_dir, f"{workflow_job_id}.zip")
        self.put_file(local_src=local_src_slurm_zip, remote_dst=hpc_dst_slurm_zip)
        self.log.info(f"Put file from local src: {local_src_slurm_zip}, to remote dst: {hpc_dst_slurm_zip}")
        self.log.info(f"Leaving put_slurm_workspace, returning: {hpc_dst_slurm_zip}")
        # Zip path inside the HPC environment
        return hpc_dst_slurm_zip

    def pack_and_put_slurm_workspace(
        self,
        ocrd_workspace_dir: str,
        workflow_job_id: str,
        nextflow_script_path: str,
        tempdir_prefix: str = "slurm_workspace-"
    ) -> Tuple[str, str]:
        self.log.info(f"Entering put_slurm_workspace")
        self.log.info(f"ocrd_workspace_dir: {ocrd_workspace_dir}")
        self.log.info(f"workflow_job_id: {workflow_job_id}")
        self.log.info(f"nextflow_script_path: {nextflow_script_path}")
        self.log.info(f"tempdir_prefix: {tempdir_prefix}")

        local_src_slurm_zip = self.create_slurm_workspace_zip(
            ocrd_workspace_dir=ocrd_workspace_dir,
            workflow_job_id=workflow_job_id,
            nextflow_script_path=nextflow_script_path,
            tempdir_prefix=tempdir_prefix
        )
        self.log.info(f"Created slurm workspace zip: {local_src_slurm_zip}")

        hpc_dst = self.put_slurm_workspace(
            local_src_slurm_zip=local_src_slurm_zip,
            workflow_job_id=workflow_job_id
        )

        self.log.info(f"Leaving pack_and_put_slurm_workspace")
        return local_src_slurm_zip, hpc_dst

    def get_and_unpack_slurm_workspace(self, ocrd_workspace_dir: str, workflow_job_dir: str):
        self.log.info(f"Entering get_and_unpack_slurm_workspace")
        self.log.info(f"ocrd_workspace_dir: {ocrd_workspace_dir}")
        self.log.info(f"workflow_job_dir: {workflow_job_dir}")

        # Parse the ocrd workspace id from the dir path
        ocrd_workspace_id = ocrd_workspace_dir.split('/')[-1]
        self.log.info(f"OCR-D workspace id to be used: {ocrd_workspace_id}")
        workflow_job_id = workflow_job_dir.split('/')[-1]
        self.log.info(f"Workflow job id to be used: {workflow_job_id}")

        get_src = join(self.slurm_workspaces_dir, workflow_job_id, f"{workflow_job_id}.zip")
        get_dst = join(Path(workflow_job_dir).parent.absolute(), f"{workflow_job_id}.zip")
        self.log.info(f"Getting workflow job zip file")
        try:
            self.get_file(remote_src=get_src, local_dst=get_dst)
        except Exception as error:
            raise Exception(
                f"Error when getting workflow job zip file: {error}, get_src: {get_src}, get_dst: {get_dst}"
            )
        self.log.info(f"Got workflow job zip file from src: {get_src}, to dst: {get_dst}")

        unpack_src = get_dst
        unpack_dst = workflow_job_dir
        try:
            unpack_zip_archive(source=unpack_src, destination=unpack_dst)
        except Exception as error:
            raise Exception(
                f"Error when unpacking workflow job zip: {error}, unpack_src: {unpack_src}, unpack_dst: {unpack_dst}"
            )
        self.log.info(f"Unpacked workflow job zip from src: {unpack_src}, to dst: {unpack_dst}")

        # Remove the temporary workflow job zip
        remove(unpack_src)
        self.log.info(f"Removed the temp workflow job zip: {unpack_src}")

        # Remove the workspace dir from the local storage,
        # before transferring the results to avoid potential
        # overwrite errors or duplications
        rmtree(ocrd_workspace_dir, ignore_errors=True)
        self.log.info(f"Removed tree dirs: {ocrd_workspace_dir}")

        get_src = join(self.slurm_workspaces_dir, workflow_job_id, ocrd_workspace_id, f"{ocrd_workspace_id}.zip")
        get_dst = join(Path(ocrd_workspace_dir).parent.absolute(), f"{ocrd_workspace_id}.zip")
        self.log.info(f"Getting workspace zip file")
        try:
            self.get_file(remote_src=get_src, local_dst=get_dst)
        except Exception as error:
            raise Exception(
                f"Error when getting workspace zip file: {error}, get_src: {get_src}, get_dst: {get_dst}"
            )
        self.log.info(f"Got workspace zip file from src: {get_src}, to dst: {get_dst}")

        unpack_src = join(Path(ocrd_workspace_dir).parent.absolute(), f"{ocrd_workspace_id}.zip")
        unpack_dst = ocrd_workspace_dir
        try:
            unpack_zip_archive(source=unpack_src, destination=unpack_dst)
        except Exception as error:
            raise Exception(
                f"Error when unpacking workspace zip: {error}, unpack_src: {unpack_src}, unpack_dst: {unpack_dst}"
            )
        self.log.info(f"Unpacked workspace zip from src: {unpack_src}, to dst: {unpack_dst}")

        # Remove the temporary workspace zip
        remove(unpack_src)
        self.log.info(f"Removed the temp workspace zip: {unpack_src}")

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
                f"Error when symlink: {error}, src: {ocrd_workspace_dir}, dst: {workspace_dir_in_workflow_job}"
            )
        self.log.info(f"Symlinked from src: {ocrd_workspace_dir}, to dst: {workspace_dir_in_workflow_job}")
        self.log.info(f"Leaving get_and_unpack_slurm_workspace")

    def mkdir_p(self, remotepath, mode=0o766):
        if remotepath == '/':
            self.sftp_client.chdir('/')  # absolute path so change directory to root
            return False
        if remotepath == '':
            return False  # top-level relative directory must exist
        try:
            self.sftp_client.chdir(remotepath)  # subdirectory exists
        except IOError as error:
            dir_name, base_name = split(remotepath.rstrip('/'))
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
        self.mkdir_p(remotepath=str(Path(remote_dst).parent.absolute()))
        self.sftp_client.put(localpath=local_src, remotepath=remote_dst)

    def put_dir(self, local_src, remote_dst, mode=0o766):
        """
        Uploads the contents of the local source directory to the remote destination directory.
        The remote destination directory needs to exist.
        All subdirectories in source are created under destination.
        """
        self.mkdir_p(remotepath=remote_dst, mode=mode)
        for item in listdir(local_src):
            item_src = join(local_src, item)
            item_dst = join(remote_dst, item)
            if isdir(item_src):
                self.put_dir(local_src=item_src, remote_dst=item_dst, mode=mode)
            else:
                self.sftp_client.chdir(remote_dst)
                self.put_file(local_src=item_src, remote_dst=item_dst)
