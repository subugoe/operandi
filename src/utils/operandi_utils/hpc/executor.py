from os.path import exists, isfile
import paramiko
from time import sleep

from .constants import (
    OPERANDI_HPC_HOST,
    OPERANDI_HPC_HOST_PROXY,
    OPERANDI_HPC_USERNAME,
    OPERANDI_HPC_SSH_KEYPATH
)


class HPCExecutor:
    def __init__(self):
        # TODO: Handle the exceptions properly
        self.__ssh_paramiko = None

    @staticmethod
    def create_proxy_jump(
            host=OPERANDI_HPC_HOST,
            proxy_host=OPERANDI_HPC_HOST_PROXY,
            username=OPERANDI_HPC_USERNAME,
            key_path=OPERANDI_HPC_SSH_KEYPATH
    ):
        jump_box = paramiko.SSHClient()
        jump_box.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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
            host=OPERANDI_HPC_HOST,
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

        self.__ssh_paramiko = paramiko.SSHClient()
        self.__ssh_paramiko.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__ssh_paramiko.connect(
            hostname=host,
            username=username,
            key_filename=key_path,
            sock=proxy_channel
        )

    @staticmethod
    def check_keyfile_existence(hpc_key_path):
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
            nextflow_script_path: str,
            input_file_grp: str,
            workspace_id: str,
            mets_basename: str
    ) -> str:

        nextflow_script_id = nextflow_script_path.split('/')[-1]
        command = "bash -lc"
        command += " 'sbatch"
        command += f" {batch_script_path}"
        command += f" {workflow_job_id}"
        command += f" {nextflow_script_id}"
        command += f" {input_file_grp}"
        command += f" {workspace_id}"
        command += f" {mets_basename}'"

        output, err, return_code = self.execute_blocking(command)
        slurm_job_id = output[0].strip('\n').split(' ')[-1]
        assert int(slurm_job_id)
        return slurm_job_id

    def check_slurm_job_state(self, slurm_job_id: str) -> str:
        command = "bash -lc"
        command += f" 'sacct -j {slurm_job_id} --format=jobid,state,exitcode'"
        output, err, return_code = self.execute_blocking(command)

        # Split the last line and get the second element,
        # i.e., the state element in the requested output format
        slurm_job_state = "None"
        if output:
            slurm_job_state = output[-1].split()[1]
        else:
            print(f"Output: {output}")
            print(f"Error: {err}")
            print(f"RC: {return_code}")
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
