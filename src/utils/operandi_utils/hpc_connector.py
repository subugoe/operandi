from os.path import exists, isfile
import paramiko
import SSHLibrary
from time import sleep

from .hpc_constants import (
    OPERANDI_HPC_HOST,
    OPERANDI_HPC_HOST_PROXY,
    OPERANDI_HPC_HOST_TRANSFER,
    OPERANDI_HPC_USERNAME,
    OPERANDI_HPC_SSH_KEYPATH,
    OPERANDI_HPC_HOME_PATH
)


# TODO: Refining is needed since the connections were separated
# TODO: Implement appropriate error handling
class HPCConnector:
    def __init__(self, hpc_home_path: str = OPERANDI_HPC_HOME_PATH, scp="ON", scp_preserve_times=True, mode="0755"):
        # TODO: Handle the exceptions properly
        self.scp = scp
        self.scp_preserve_times = scp_preserve_times
        self.mode = mode
        self.hpc_home_path = hpc_home_path
        self.__ssh_io_transfer = None
        self.__ssh_paramiko = None

    # This connection is used only
    # for IO transfers to/from HPC cluster
    def connect_to_hpc_io_transfer(
            self,
            host=OPERANDI_HPC_HOST_TRANSFER,
            username=OPERANDI_HPC_USERNAME,
            key_path=OPERANDI_HPC_SSH_KEYPATH
    ):
        self.__ssh_io_transfer = SSHLibrary.SSHLibrary()
        keyfile = self.__check_keyfile_existence(key_path)
        if not keyfile:
            print(f"Error: HPC key path does not exist or is not readable!")
            print(f"Checked path: \n{key_path}")
            exit(1)

        self.__ssh_io_transfer.open_connection(host=host)
        self.__ssh_io_transfer.login_with_public_key(
            username=username,
            keyfile=keyfile,
            allow_agent=True
        )

    # This connection uses proxy jump host to
    # connect to the front-end node of the HPC cluster
    def connect_to_hpc(
            self,
            host=OPERANDI_HPC_HOST,
            proxy_host=OPERANDI_HPC_HOST_PROXY,
            username=OPERANDI_HPC_USERNAME,
            key_path=OPERANDI_HPC_SSH_KEYPATH
    ):
        jump_box_public_addr = proxy_host
        jump_box_private_addr = host
        target_addr = host

        jump_box = paramiko.SSHClient()
        jump_box.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jump_box.connect(
            jump_box_public_addr,
            username=username,
            key_filename=key_path
        )

        jump_box_channel = jump_box.get_transport().open_channel(
            "direct-tcpip",
            (jump_box_private_addr, 22),
            (target_addr, 22)
        )

        self.__ssh_paramiko = paramiko.SSHClient()
        self.__ssh_paramiko.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__ssh_paramiko.connect(
            target_addr,
            username=username,
            key_filename=key_path,
            sock=jump_box_channel
        )

    @staticmethod
    def __check_keyfile_existence(hpc_key_path):
        if exists(hpc_key_path) and isfile(hpc_key_path):
            return hpc_key_path
        return None

    # TODO: Handle the output and return_code instead of just returning them
    # Execute blocking commands
    # Waiting for an output and return_code
    def execute_blocking(self, command, timeout=None, environment=None):
        stdin, stdout, stderr = self.__ssh_paramiko.exec_command(
            command=command,
            timeout=timeout,
            environment=environment
        )

        # TODO: Not satisfied with this but fast conversion from
        #  SSHLibrary to Paramiko is needed for testing
        while not stdout.channel.exit_status_ready():
            sleep(1)
            continue

        output = stdout.readlines()
        err = stderr.readlines()
        return_code = stdout.channel.recv_exit_status()
        return output, err, return_code

    def trigger_slurm_job(
            self,
            batch_script_path: str,
            workflow_job_id: str,
            nextflow_script_id: str,
            input_file_grp: str
    ) -> str:

        command = "bash -lc"
        command += " 'sbatch"
        command += f" {batch_script_path}"
        command += f" {workflow_job_id}"
        command += f" {nextflow_script_id}"
        command += f" {input_file_grp}'"

        output, err, return_code = self.execute_blocking(command)
        slurm_job_id = output[0].strip('\n').split(' ')[-1]
        # print(f"output: \n{output}")
        # print(f"err: \n{err}")
        # print(f"return_code: [{return_code}]")
        # print(f"slurm_job_id: [{slurm_job_id}]")
        assert int(slurm_job_id)
        return slurm_job_id

    def check_slurm_job_state(self, slurm_job_id: str) -> str:
        command = "bash -lc"
        command += f" 'sacct -j {slurm_job_id} --format=jobid,state,exitcode'"
        output, err, return_code = self.execute_blocking(command)

        # Split the last line and get the second element,
        # i.e., the state element in the requested output format
        slurm_job_state = output[-1].split()[1]
        return slurm_job_state

    def poll_till_end_slurm_job_state(self, slurm_job_id: str, interval: int = 5, timeout: int = 300) -> bool:
        # TODO: Create a separate SlurmJob class
        slurm_fail_states = ["BOOT_FAIL", "CANCELLED", "DEADLINE", "FAILED", "NODE_FAIL",
                             "OUT_OF_MEMORY", "PREEMPTED", "REVOKED", "TIMEOUT"]
        slurm_success_states = ["COMPLETED"]
        slurm_waiting_states = ["RUNNING", "PENDING", "COMPLETING", "REQUEUED", "RESIZING", "SUSPENDED"]

        tries_left = timeout/interval
        while tries_left:
            sleep(interval)
            tries_left -= 1
            slurm_job_state = self.check_slurm_job_state(slurm_job_id)
            if slurm_job_state in slurm_success_states:
                return True
            if slurm_job_state in slurm_waiting_states:
                continue
            if slurm_job_state in slurm_fail_states:
                return False
            raise ValueError(f"Invalid SLURM job state: {slurm_job_state}")

        # Timeout reached
        return False

    def put_file(self, source, destination):
        self.__ssh_io_transfer.put_file(
            source=source,
            destination=destination,
            mode=self.mode,
            scp=self.scp,
            scp_preserve_times=self.scp_preserve_times
        )

    def put_directory(self, source, destination, recursive=True):
        self.__ssh_io_transfer.put_directory(
            source=source,
            destination=destination,
            mode=self.mode,
            recursive=recursive,
            scp=self.scp,
            scp_preserve_times=self.scp_preserve_times
        )

    def get_file(self, source, destination):
        self.__ssh_io_transfer.get_file(
            source=source,
            destination=destination,
            scp=self.scp,
            scp_preserve_times=self.scp_preserve_times
        )

    def get_directory(self, source, destination, recursive=True):
        self.__ssh_io_transfer.get_directory(
            source=source,
            destination=destination,
            recursive=recursive,
            scp=self.scp,
            scp_preserve_times=self.scp_preserve_times
        )
