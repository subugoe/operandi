from os import (
    listdir,
    makedirs,
    remove,
    symlink
)
from os.path import (
    dirname,
    exists,
    join,
    isdir,
    isfile,
    split
)
from paramiko import AutoAddPolicy, SSHClient
from pathlib import Path
from shutil import rmtree, copytree
from stat import S_ISDIR
from tempfile import mkdtemp
from typing import Tuple

from operandi_utils import make_zip_archive, unpack_zip_archive
from .constants import (
    OPERANDI_HPC_DIR_BATCH_SCRIPTS,
    OPERANDI_HPC_DIR_SLURM_WORKSPACES,
    OPERANDI_HPC_HOST_TRANSFER,
    OPERANDI_HPC_HOST_TRANSFER_PROXY,
    OPERANDI_HPC_HOST_PROXY,
    OPERANDI_HPC_USERNAME,
    OPERANDI_HPC_SSH_KEYPATH
)


class HPCTransfer:
    def __init__(self):
        # TODO: Handle the exceptions properly
        self.__ssh_paramiko = None
        self.sftp = None

    @staticmethod
    def create_proxy_jump(
            host=OPERANDI_HPC_HOST_TRANSFER,
            proxy_host=OPERANDI_HPC_HOST_TRANSFER_PROXY,
            username=OPERANDI_HPC_USERNAME,
            key_path=OPERANDI_HPC_SSH_KEYPATH
    ):
        jump_box = SSHClient()
        jump_box.set_missing_host_key_policy(AutoAddPolicy())
        jump_box.connect(
            proxy_host,
            username=username,
            key_filename=key_path
        )
        jump_box_channel = jump_box.get_transport().open_channel(
            kind="direct-tcpip",
            dest_addr=(host, 22),
            src_addr=(proxy_host, 22)
        )
        return jump_box_channel

    # This connection uses proxy jump host to
    # connect to the front-end node of the HPC cluster
    def connect(
            self,
            host=OPERANDI_HPC_HOST_TRANSFER,
            proxy_host=OPERANDI_HPC_HOST_PROXY,
            username=OPERANDI_HPC_USERNAME,
            key_path=OPERANDI_HPC_SSH_KEYPATH
    ):
        keyfile = self.check_keyfile_existence(key_path)
        if not keyfile:
            print(f"Error: HPC key path does not exist or is not readable!")
            print(f"Checked path: \n{key_path}")
            exit(1)

        proxy_channel = self.create_proxy_jump(
            host=host,
            proxy_host=proxy_host,
            username=username,
            key_path=key_path
        )
        self.__ssh_paramiko = SSHClient()
        self.__ssh_paramiko.set_missing_host_key_policy(AutoAddPolicy())
        self.__ssh_paramiko.connect(
            hostname=host,
            username=username,
            key_filename=key_path,
            sock=proxy_channel,
            allow_agent=False,
            look_for_keys=False
        )

        self.sftp = self.__ssh_paramiko.open_sftp()

    @staticmethod
    def check_keyfile_existence(hpc_key_path):
        if exists(hpc_key_path) and isfile(hpc_key_path):
            return hpc_key_path
        return None

    def put_batch_script(self, batch_script_id: str) -> str:
        local_batch_script_path = join(dirname(__file__), "batch_scripts", batch_script_id)
        hpc_batch_script_path = join(OPERANDI_HPC_DIR_BATCH_SCRIPTS, batch_script_id)
        self.put_file(
            local_src=local_batch_script_path,
            remote_dst=hpc_batch_script_path
        )
        return hpc_batch_script_path

    def pack_and_put_slurm_workspace(
            self,
            ocrd_workspace_id: str,
            ocrd_workspace_dir: str,
            workflow_job_id: str,
            nextflow_script_path: str = None,
            nextflow_filename: str = "default_workflow.nf",
            tempdir_prefix: str = "slurm_workspace-"
    ) -> Tuple[str, str]:
        # If no nextflow script is provided, then the default one is used
        if not nextflow_script_path:
            nextflow_script_path = join(dirname(__file__), "nextflow_workflows", nextflow_filename)

        tempdir = mkdtemp(prefix=tempdir_prefix)
        temp_workflow_job_dir = join(join(tempdir, workflow_job_id))
        makedirs(temp_workflow_job_dir)

        symlink(
            src=nextflow_script_path,
            dst=join(temp_workflow_job_dir, nextflow_filename),
        )
        copytree(
            src=ocrd_workspace_dir,
            dst=join(temp_workflow_job_dir, ocrd_workspace_id)
        )
        make_zip_archive(temp_workflow_job_dir, f"{temp_workflow_job_dir}.zip")
        self.put_file(
            local_src=f"{temp_workflow_job_dir}.zip",
            remote_dst=join(OPERANDI_HPC_DIR_SLURM_WORKSPACES, f"{workflow_job_id}.zip")
        )

        # Zip path inside the HPC environment
        return OPERANDI_HPC_DIR_SLURM_WORKSPACES, nextflow_filename

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
            self.get_file(remote_src=get_src, local_dst=get_dst)
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
            self.get_file(remote_src=get_src, local_dst=get_dst)
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
                f"error when symlink: {error}, src: {ocrd_workspace_dir}, dst: {workspace_dir_in_workflow_job}"
            )

    def mkdir_p(self, remotepath, mode=0o766):
        if remotepath == '/':
            self.sftp.chdir('/')  # absolute path so change directory to root
            return False
        if remotepath == '':
            return False  # top-level relative directory must exist
        try:
            self.sftp.chdir(remotepath)  # subdirectory exists
        except IOError as error:
            dir_name, base_name = split(remotepath.rstrip('/'))
            self.mkdir_p(dir_name)  # make parent directories
            self.sftp.mkdir(path=base_name, mode=mode)  # subdirectory missing, so created it
            self.sftp.chdir(base_name)
            return True

    def get_file(self, remote_src, local_dst):
        self.sftp.get(remotepath=remote_src, localpath=local_dst)

    def get_dir(self, remote_src, local_dst, mode=0o766):
        """
        Downloads the contents of the remote source directory to the local destination directory.
        The remote source directory needs to exist.
        All subdirectories in source are created under destination.
        """
        for item in self.sftp.listdir(remote_src):
            item_src = join(remote_src, item)
            item_dst = join(local_dst, item)
            if S_ISDIR(self.sftp.lstat(item_src).st_mode):
                makedirs(name=item_dst, mode=mode, exist_ok=True)
                self.get_dir(remote_src=item_src, local_dst=item_dst, mode=mode)
            else:
                self.get_file(remote_src=item_src, local_dst=item_dst)

    def put_file(self, local_src, remote_dst):
        self.mkdir_p(remotepath=str(Path(remote_dst).parent.absolute()))
        self.sftp.put(localpath=local_src, remotepath=remote_dst)

    def put_dir(self, local_src, remote_dst, mode=0o766):
        """
        Uploads the contents of the local source directory to the remote destination directory.
        The remote destination directory needs to exist.
        All subdirectories in source are created under destination.
        """
        for item in listdir(local_src):
            item_src = join(local_src, item)
            item_dst = join(remote_dst, item)
            if isdir(item_src):
                self.mkdir_p(remotepath=item_dst, mode=mode)
                self.put_dir(local_src=item_src, remote_dst=item_dst, mode=mode)
            else:
                self.sftp.chdir(remote_dst)
                self.put_file(local_src=item_src, remote_dst=item_dst)
