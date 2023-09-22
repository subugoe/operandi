from os.path import exists, isfile
import paramiko
from time import sleep
import logging

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
        self.log = logging.getLogger(__name__)

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
        self.check_keyfile_existence(key_path)
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
        if not exists(hpc_key_path):
            raise FileNotFoundError(f"HPC key path does not exists: {hpc_key_path}")
        if not isfile(hpc_key_path):
            raise FileNotFoundError(f"HPC key path is not a file: {hpc_key_path}")

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
            mets_basename: str,
            cpus: int,
            ram: int
    ) -> str:

        nextflow_script_id = nextflow_script_path.split('/')[-1]
        command = "bash -lc"
        command += " 'sbatch"

        # SBATCH arguments passed to the batch script
        command += f" --cpus-per-task={cpus}"
        command += f" --mem={ram}G"

        # Regular arguments passed to the batch script
        command += f" {batch_script_path}"
        command += f" {workflow_job_id}"
        command += f" {nextflow_script_id}"
        command += f" {input_file_grp}"
        command += f" {workspace_id}"
        command += f" {mets_basename}"
        command += f" {cpus}"
        command += f" {ram}GB"
        command += "'"

        self.log.info(f"About to execute a blocking command: {command}")
        output, err, return_code = self.execute_blocking(command)
        self.log.info(f"Command output: {output}")
        self.log.info(f"Command err: {err}")
        self.log.info(f"Command return code: {return_code}")
        slurm_job_id = output[0].strip('\n').split(' ')[-1]
        self.log.info(f"Slurm job id: {slurm_job_id}")
        assert int(slurm_job_id)
        return slurm_job_id

    def check_slurm_job_state(self, slurm_job_id: str) -> str:
        command = "bash -lc"
        command += f" 'sacct -j {slurm_job_id} --format=jobid,state,exitcode'"

        self.log.info(f"About to execute a blocking command: {command}")
        output, err, return_code = self.execute_blocking(command)
        self.log.info(f"Command output: {output}")
        self.log.info(f"Command err: {err}")
        self.log.info(f"Command return code: {return_code}")

        # Split the last line and get the second element,
        # i.e., the state element in the requested output format
        slurm_job_state = None
        if output:
            slurm_job_state = output[-1].split()[1]
        self.log.info(f"Slurm job state: {slurm_job_state}")
        return slurm_job_state

    def poll_till_end_slurm_job_state(self, slurm_job_id: str, interval: int = 5, timeout: int = 300) -> bool:
        self.log.info(f"Polling slurm job status till end")
        # TODO: Create a separate SlurmJob class
        slurm_fail_states = ["BOOT_FAIL", "CANCELLED", "DEADLINE", "FAILED", "NODE_FAIL",
                             "OUT_OF_MEMORY", "PREEMPTED", "REVOKED", "TIMEOUT"]
        slurm_success_states = ["COMPLETED"]
        slurm_waiting_states = ["RUNNING", "PENDING", "COMPLETING", "REQUEUED", "RESIZING", "SUSPENDED"]

        tries_left = timeout/interval
        self.log.info(f"Tries to be performed: {tries_left}")
        while tries_left:
            self.log.info(f"Sleeping for {interval} secs")
            sleep(interval)
            tries_left -= 1
            self.log.info(f"Tries left: {tries_left}")
            slurm_job_state = self.check_slurm_job_state(slurm_job_id)
            if not slurm_job_state:
                self.log.info(f"Slurm job state is not available yet")
                continue
            if slurm_job_state in slurm_success_states:
                self.log.info(f"Slurm job state is in: {slurm_success_states}")
                self.log.info(f"Returning True")
                return True
            if slurm_job_state in slurm_waiting_states:
                self.log.info(f"Slurm job state is in: {slurm_waiting_states}")
                continue
            if slurm_job_state in slurm_fail_states:
                self.log.info(f"Slurm job state is in: {slurm_fail_states}")
                self.log.info(f"Returning False")
                return False
            # Sometimes the slurm state is still
            # not initialized inside the HPC environment.
            # This is not a problem that requires a raise of Exception
            self.log.warning(f"Invalid SLURM job state: {slurm_job_state}")

        # Timeout reached
        self.log.info("Polling slurm job status timeout reached")
        self.log.info(f"Returning False")
        return False
