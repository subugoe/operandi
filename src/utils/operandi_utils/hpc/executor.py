from logging import getLogger
from os import environ
from pathlib import Path
from time import sleep
from typing import List
from .connector import HPCConnector
from .constants import HPC_EXECUTOR_HOSTS, HPC_EXECUTOR_PROXY_HOSTS


class HPCExecutor(HPCConnector):
    def __init__(
        self,
        executor_hosts: List[str] = HPC_EXECUTOR_HOSTS,
        proxy_hosts: List[str] = HPC_EXECUTOR_PROXY_HOSTS,
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
            hpc_hosts=executor_hosts,
            proxy_hosts=proxy_hosts,
            project_name=project_name,
            log=getLogger("operandi_utils.hpc.executor"),
            username=username,
            key_path=Path(key_path),
            key_pass=None
        )

    # TODO: Handle the output and return_code instead of just returning them
    # Execute blocking commands
    # Waiting for an output and return_code
    def execute_blocking(self, command, timeout=None, environment=None):
        self.reconnect_if_required()
        stdin, stdout, stderr = self.ssh_hpc_client.exec_command(
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
        job_deadline_time: str,
        cpus: int,
        ram: int,
        nf_process_forks: int,
        ws_pages_amount: int
    ) -> str:

        nextflow_script_id = nextflow_script_path.split('/')[-1]
        command = "bash -lc"
        command += " 'sbatch"

        if ws_pages_amount < nf_process_forks:
            self.log.warning(
                "The amount of workspace pages is less than the amount of requested Nextflow process forks. "
                f"The pages amount: {ws_pages_amount}, forks requested: {nf_process_forks}. "
                f"Setting the forks value to the value of amount of pages."
            )
            nf_process_forks = ws_pages_amount

        # SBATCH arguments passed to the batch script
        command += f" --partition medium"
        command += f" --time={job_deadline_time}"
        command += f" --output={self.project_root_dir}/slurm-job-%J.txt"
        command += f" --cpus-per-task={cpus}"
        command += f" --mem={ram}G"

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

    def check_slurm_job_state(self, slurm_job_id: str, tries: int = 3, wait_time: int = 2) -> str:
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
                slurm_job_state = output[-1].split()[1]
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
