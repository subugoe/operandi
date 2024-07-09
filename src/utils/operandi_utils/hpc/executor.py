from logging import getLogger
from os import environ
from pathlib import Path
from time import sleep
from typing import List
from operandi_utils.constants import StateJobSlurm
from .connector import HPCConnector
from .constants import (
    HPC_EXECUTOR_HOSTS, HPC_EXECUTOR_PROXY_HOSTS, HPC_JOB_DEADLINE_TIME_TEST, HPC_JOB_QOS_REGULAR,
    HPC_JOB_DEFAULT_PARTITION
)


class HPCExecutor(HPCConnector):
    def __init__(
        self,
        executor_hosts: List[str] = HPC_EXECUTOR_HOSTS, proxy_hosts: List[str] = HPC_EXECUTOR_PROXY_HOSTS,
        username: str = environ.get("OPERANDI_HPC_USERNAME", None),
        project_username: str = environ.get("OPERANDI_HPC_PROJECT_USERNAME", None),
        key_path: str = environ.get("OPERANDI_HPC_SSH_KEYPATH", None),
        project_name: str = environ.get("OPERANDI_HPC_PROJECT_NAME", None),
        tunnel_host: str = 'localhost', tunnel_port: int = 0
    ) -> None:
        if not username:
            raise ValueError("Environment variable not set: OPERANDI_HPC_USERNAME")
        if not project_username:
            raise ValueError("Environment variable not set: OPERANDI_HPC_PROJECT_USERNAME")
        if not key_path:
            raise ValueError("Environment variable not set: OPERANDI_HPC_SSH_KEYPATH")
        if not project_name:
            raise ValueError("Environment variable not set: OPERANDI_HPC_PROJECT_NAME")
        super().__init__(
            hpc_hosts=executor_hosts, proxy_hosts=proxy_hosts, project_name=project_name,
            log=getLogger("operandi_utils.hpc.executor"), username=username, project_username=project_username,
            key_path=Path(key_path), key_pass=None, tunnel_host=tunnel_host, tunnel_port=tunnel_port
        )

    # TODO: Handle the output and return_code instead of just returning them
    # Execute blocking commands
    # Waiting for an output and return_code
    def execute_blocking(self, command, timeout=None, environment=None):
        self.reconnect_if_required()
        stdin, stdout, stderr = self.ssh_hpc_client.exec_command(
            command=command, timeout=timeout, environment=environment)

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
        self, batch_script_path: str, workflow_job_id: str, nextflow_script_path: str, input_file_grp: str,
        workspace_id: str, mets_basename: str, nf_process_forks: int, ws_pages_amount: int, use_mets_server: bool,
        file_groups_to_remove: str, cpus: int = 2, ram: int = 8, job_deadline_time: str = HPC_JOB_DEADLINE_TIME_TEST,
        partition: str = HPC_JOB_DEFAULT_PARTITION, qos: str = HPC_JOB_QOS_REGULAR
    ) -> str:
        nextflow_script_id = nextflow_script_path.split('/')[-1]
        command = "bash -lc"
        command += f" 'sbatch"

        if ws_pages_amount < nf_process_forks:
            self.log.warning(
                "The amount of workspace pages is less than the amount of requested Nextflow process forks. "
                f"The pages amount: {ws_pages_amount}, forks requested: {nf_process_forks}. "
                f"Setting the forks value to the value of amount of pages.")
            nf_process_forks = ws_pages_amount

        # SBATCH arguments passed to the batch script
        command += f" --partition={partition}"
        command += f" --time={job_deadline_time}"
        command += f" --output={self.project_root_dir}/slurm-job-%J.txt"
        command += f" --cpus-per-task={cpus}"
        command += f" --mem={ram}G"

        if qos != HPC_JOB_QOS_REGULAR:
            command += f" --qos={qos}"

        # Regular arguments passed to the batch script
        command += f" {batch_script_path}"
        command += f" {self.slurm_workspaces_dir}"
        command += f" {workflow_job_id}"
        command += f" {nextflow_script_id}"
        command += f" {input_file_grp}"
        command += f" {workspace_id}"
        command += f" {mets_basename}"
        command += f" {cpus}"
        command += f" {ram}"
        command += f" {nf_process_forks}"
        command += f" {ws_pages_amount}"
        use_mets_server_bash_flag = "true" if use_mets_server else "false"
        command += f" {use_mets_server_bash_flag}"
        command += f" {file_groups_to_remove}"
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

    def check_slurm_job_state(self, slurm_job_id: str, tries: int = 10, wait_time: int = 2) -> str:
        command = "bash -lc"
        command += f" 'sacct -j {slurm_job_id} --format=jobid,state,exitcode'"
        slurm_job_state = None

        while not slurm_job_state and tries > 0:
            self.log.info(f"About to execute a blocking command: {command}")
            output, err, return_code = self.execute_blocking(command)
            self.log.info(f"Command output: {output}")
            self.log.info(f"Command err: {err}")
            self.log.info(f"Command return code: {return_code}")
            if output:
                # Split the last line and get the second element,
                # i.e., the state element in the requested output format
                slurm_job_state = output[-2].split()[1]
                # TODO: dirty fast fix, improve this
                if slurm_job_state == '----------':
                    slurm_job_state = None
                    continue
            if slurm_job_state:
                break
            tries -= 1
            sleep(wait_time)
        if not slurm_job_state:
            self.log.warning(f"Returning a None slurm job state")
        self.log.info(f"Slurm job state of {slurm_job_id}: {slurm_job_state}")
        return slurm_job_state

    def poll_till_end_slurm_job_state(self, slurm_job_id: str, interval: int = 5, timeout: int = 300) -> bool:
        self.log.info(f"Polling slurm job status till end")
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
            if StateJobSlurm.is_state_success(slurm_job_state):
                self.log.info(f"Slurm job state is in: {StateJobSlurm.success_states()}")
                return True
            if StateJobSlurm.is_state_waiting(slurm_job_state):
                self.log.info(f"Slurm job state is in: {StateJobSlurm.waiting_states()}")
                continue
            if StateJobSlurm.is_state_fail(slurm_job_state):
                self.log.info(f"Slurm job state is in: {StateJobSlurm.failing_states()}")
                return False
            # Sometimes the slurm state is still
            # not initialized inside the HPC environment.
            # This is not a problem that requires a raise of Exception
            self.log.warning(f"Invalid SLURM job state: {slurm_job_state}")

        # Timeout reached
        self.log.info("Polling slurm job status timeout reached")
        return False
