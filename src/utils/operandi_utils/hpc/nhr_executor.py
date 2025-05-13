from json import dumps
from logging import getLogger
from os.path import join
from pathlib import Path
from time import sleep
from typing import List

from operandi_utils.constants import StateJobSlurm, OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE
from .constants import (
    HPC_JOB_DEADLINE_TIME_TEST, HPC_JOB_QOS_DEFAULT, HPC_NHR_JOB_DEFAULT_PARTITION, HPC_BATCH_SUBMIT_WORKFLOW_JOB,
    HPC_WRAPPER_SUBMIT_WORKFLOW_JOB, HPC_WRAPPER_CHECK_WORKFLOW_JOB_STATUS
)
from .nhr_connector import NHRConnector
from .nhr_executor_cmd_wrappers import cmd_nextflow_run
from .nhr_executor_utils import parse_slurm_job_state_from_output

CHECK_SLURM_JOB_TRY_TIMES = 10
CHECK_SLURM_JOB_WAIT_TIME = 30
POLL_SLURM_JOB_TIMEOUT = 300
POLL_SLURM_JOB_CHECK_INTERVAL = 10

class NHRExecutor(NHRConnector):
    def __init__(self) -> None:
        logger = getLogger(name=self.__class__.__name__)
        super().__init__(logger)
        _ = self.ssh_client  # forces a connection

    def make_remote_batch_scripts_executable(self):
        hpc_slurm_job_dir = f"{self.batch_scripts_dir}"
        command = f"bash -lc 'chmod +x -R {hpc_slurm_job_dir}'"
        self.logger.info(f"About to execute a force command: {command}")
        output, err, return_code = self.execute_blocking(command)
        self.logger.info(f"Command output: {output}")
        self.logger.info(f"Command err: {err}")
        self.logger.info(f"Command return code: {return_code}")

    # Execute blocking commands and wait for an output and return code
    def execute_blocking(self, command, timeout=None, environment=None):
        stdin, stdout, stderr = self.ssh_client.exec_command(command=command, timeout=timeout, environment=environment)
        while not stdout.channel.exit_status_ready():
            sleep(1)
            continue
        output, err = stdout.readlines(), stderr.readlines()
        return_code = stdout.channel.recv_exit_status()
        return output, err, return_code

    def remove_workflow_job_dir(self, workflow_job_id: str):
        hpc_slurm_job_dir = f"{self.slurm_workspaces_dir}/{workflow_job_id}"
        command = f"bash -lc 'rm -rf {hpc_slurm_job_dir}'"
        self.logger.info(f"About to execute a force command: {command}")
        output, err, return_code = self.execute_blocking(command)
        self.logger.info(f"Command output: {output}")
        self.logger.info(f"Command err: {err}")
        self.logger.info(f"Command return code: {return_code}")

    def check_if_model_exists(self, ocrd_processor: str, model: str) -> bool:
        model_path = f"{self.project_root_dir}/ocrd_models/ocrd-resources/{ocrd_processor}/{model}"
        command = f"bash -lc 'ls -la {model_path}'"
        self.logger.info(f"About to execute a force command: {command}")
        output, err, return_code = self.execute_blocking(command)
        self.logger.info(f"Command output: {output}")
        self.logger.info(f"Command err: {err}")
        self.logger.info(f"Command return code: {return_code}")
        return not bool(return_code)

    def trigger_slurm_job(
        self, workflow_job_id: str, nextflow_script_path: Path, input_file_grp: str,
        workspace_id: str, mets_basename: str, nf_process_forks: int, ws_pages_amount: int, use_mets_server: bool,
        nf_executable_steps: List[str], file_groups_to_remove: str, cpus: int = 2, ram: int = 8,
        job_deadline_time: str = HPC_JOB_DEADLINE_TIME_TEST, partition: str = HPC_NHR_JOB_DEFAULT_PARTITION,
        qos: str = HPC_JOB_QOS_DEFAULT
    ) -> str:
        if ws_pages_amount < nf_process_forks:
            self.logger.warning(
                "The amount of workspace pages is less than the amount of requested Nextflow process forks. "
                f"The pages amount: {ws_pages_amount}, forks requested: {nf_process_forks}. "
                f"Setting the forks value to the value of amount of pages.")
            nf_process_forks = ws_pages_amount

        force_command = f"{join(self.batch_scripts_dir, HPC_WRAPPER_SUBMIT_WORKFLOW_JOB)}"
        sbatch_args = {
            "constraint": "ssd",
            "partition": partition,
            "job_deadline_time": job_deadline_time,
            "output_log": f"{self.slurm_workspaces_dir}/{workflow_job_id}/slurm-job-%J.txt",
            "cpus": cpus,
            "ram": f"{ram}G",
            "qos": qos,
            "batch_script_path": join(self.batch_scripts_dir, HPC_BATCH_SUBMIT_WORKFLOW_JOB)
        }

        sif_ocrd_core = OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE["ocrd"]
        nf_run_command = cmd_nextflow_run(
            sif_core=sif_ocrd_core, input_file_grp=input_file_grp,
            mets_basename=mets_basename, use_mets_server=use_mets_server, nf_executable_steps=nf_executable_steps,
            ws_pages_amount=ws_pages_amount, cpus=cpus, ram=ram, forks=nf_process_forks
        )

        ocrd_processor_images = ",".join([OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE[exe] for exe in nf_executable_steps])
        ocrd_processor_images = f"{sif_ocrd_core},{ocrd_processor_images}"
        regular_args = {
            "ocrd_processor_images": ocrd_processor_images,
            "project_base_dir": self.project_root_dir,
            "scratch_base_dir": self.slurm_workspaces_dir,
            "use_mets_server": "true" if use_mets_server else "false",
            "workflow_job_id": workflow_job_id,
            "workspace_id": workspace_id,
            "nf_script_id": nextflow_script_path.name,
            "file_groups_to_remove": file_groups_to_remove,
            "sif_ocrd_core": sif_ocrd_core,
            "nf_run_command": nf_run_command
        }
        force_command += f" '{dumps(sbatch_args)}' '{dumps(regular_args)}'"

        self.logger.info(f"About to execute a force command: {force_command}")
        output, err, return_code = self.execute_blocking(force_command)
        self.logger.info(f"Force command output: {output}")
        self.logger.info(f"Force command err: {err}")
        self.logger.info(f"Force command return code: {return_code}")
        slurm_job_id = output[0].strip('\n').split(' ')[-1]
        self.logger.info(f"Slurm job id: {slurm_job_id}")
        assert int(slurm_job_id)
        return slurm_job_id

    def check_slurm_job_state_once(self, slurm_job_id: str) -> StateJobSlurm:
        force_command = f"{join(self.batch_scripts_dir, HPC_WRAPPER_CHECK_WORKFLOW_JOB_STATUS)} {slurm_job_id}"
        output, err, return_code = self.execute_blocking(force_command)
        if return_code > 0:
            self.logger.info(f"Executed force command: {force_command}")
            self.logger.info(f"Force command return code: {return_code}")
            self.logger.info(f"Force command err: {err}")
            self.logger.info(f"Force command output: {output}")
        slurm_job_state, msg = parse_slurm_job_state_from_output(output)
        if slurm_job_state == StateJobSlurm.UNSET:
            self.logger.warning(msg)
        return slurm_job_state

    def check_slurm_job_state(
        self, slurm_job_id: str, tries: int = CHECK_SLURM_JOB_TRY_TIMES, wait_time: int = CHECK_SLURM_JOB_WAIT_TIME
    ) -> str:
        slurm_job_state = StateJobSlurm.UNSET
        while tries > 0:
            slurm_job_state = self.check_slurm_job_state_once(slurm_job_id=slurm_job_id)
            if slurm_job_state != StateJobSlurm.UNSET:
                break
            tries -= 1
            sleep(wait_time)
        self.logger.info(f"Current slurm job state of {slurm_job_id}: {slurm_job_state}")
        return slurm_job_state

    def poll_till_end_slurm_job_state(
        self, slurm_job_id: str, interval: int = POLL_SLURM_JOB_CHECK_INTERVAL, timeout: int = POLL_SLURM_JOB_TIMEOUT
    ) -> bool:
        self.logger.info(f"Polling slurm job status till end")
        tries_left = timeout / interval
        self.logger.info(f"Tries to be performed: {tries_left}")
        while tries_left:
            self.logger.info(f"Sleeping for {interval} seconds, before trying again")
            sleep(interval)
            tries_left -= 1
            self.logger.info(f"Tries left: {tries_left}")
            slurm_job_state = self.check_slurm_job_state(slurm_job_id)
            if slurm_job_state == StateJobSlurm.UNSET:
                self.logger.info(f"Slurm job state is not available yet")
                continue
            if StateJobSlurm.is_state_hpc_success(slurm_job_state):
                self.logger.info(f"Slurm job state is in: {StateJobSlurm.success_states()}")
                return True
            if StateJobSlurm.is_state_waiting(slurm_job_state):
                self.logger.info(f"Slurm job state is in: {StateJobSlurm.waiting_states()}")
                continue
            if StateJobSlurm.is_state_running(slurm_job_state):
                self.logger.info(f"Slurm job state is in: {StateJobSlurm.running_states()}")
                continue
            if StateJobSlurm.is_state_hpc_fail(slurm_job_state):
                self.logger.info(f"Slurm job state is in: {StateJobSlurm.failing_states()}")
                return False
        # Timeout reached
        self.logger.warning("Polling slurm job status timeout reached")
        return False
