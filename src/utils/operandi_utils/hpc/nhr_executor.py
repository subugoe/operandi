from json import dumps
from logging import getLogger
from os.path import join
from pathlib import Path
from time import sleep
from typing import List

from operandi_utils.constants import StateJobSlurm, OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE
from .constants import (
    HPC_JOB_DEADLINE_TIME_TEST, HPC_JOB_QOS_DEFAULT, HPC_NHR_JOB_DEFAULT_PARTITION, HPC_BATCH_SUBMIT_WORKFLOW_JOB,
    HPC_USE_SLIM_IMAGES, HPC_WRAPPER_SUBMIT_WORKFLOW_JOB, HPC_WRAPPER_CHECK_WORKFLOW_JOB_STATUS
)
from .nhr_connector import NHRConnector

# Just some placeholders to be replaced with actual paths that are
# dynamically allocated inside the node that runs the HPC slurm job
PH_NODE_DIR_OCRD_MODELS = "PH_NODE_DIR_OCRD_MODELS"
PH_NODE_DIR_PROCESSOR_SIFS = "PH_NODE_DIR_PROCESSOR_SIFS"
PH_CMD_WRAPPER = "PH_CMD_WRAPPER"

CHECK_SLURM_JOB_TRY_TIMES = 10
CHECK_SLURM_JOB_WAIT_TIME = 30
POLL_SLURM_JOB_TIMEOUT = 300
POLL_SLURM_JOB_CHECK_INTERVAL = 10

class NHRExecutor(NHRConnector):
    def __init__(self) -> None:
        logger = getLogger(name=self.__class__.__name__)
        super().__init__(logger)
        _ = self.ssh_client  # forces a connection

    # Execute blocking commands and wait for an output and return code
    def execute_blocking(self, command, timeout=None, environment=None):
        stdin, stdout, stderr = self.ssh_client.exec_command(
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

    def remove_workflow_job_dir(self, workflow_job_id: str):
        hpc_slurm_job_dir = f"{self.slurm_workspaces_dir}/{workflow_job_id}"
        command = f"bash -lc 'rm -rf {hpc_slurm_job_dir}'"
        self.logger.info(f"About to execute a force command: {command}")
        output, err, return_code = self.execute_blocking(command)
        self.logger.info(f"Command output: {output}")
        self.logger.info(f"Command err: {err}")
        self.logger.info(f"Command return code: {return_code}")

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

        nextflow_script_id = nextflow_script_path.name
        use_mets_server_bash_flag = "true" if use_mets_server else "false"

        command = f"{HPC_WRAPPER_SUBMIT_WORKFLOW_JOB}"
        sbatch_args = {
            "partition": partition,
            "job_deadline_time": job_deadline_time,
            "output_log": f"{self.slurm_workspaces_dir}/{workflow_job_id}/slurm-job-%J.txt",
            "cpus": cpus,
            "ram": f"{ram}G",
            "qos": qos,
            "batch_script_path": HPC_BATCH_SUBMIT_WORKFLOW_JOB
        }

        hpc_workflow_job_dir = join(self.slurm_workspaces_dir, workflow_job_id)
        hpc_nf_script_path = join(self.slurm_workspaces_dir, workflow_job_id, nextflow_script_id)
        hpc_workspace_dir = join(self.slurm_workspaces_dir, workflow_job_id, workspace_id)

        sif_ocrd_all = OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE["ocrd_all"]
        sif_ocrd_core = OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE["ocrd"]

        if HPC_USE_SLIM_IMAGES:
            ph_sif_core = f"{PH_NODE_DIR_PROCESSOR_SIFS}/{sif_ocrd_core}"
        else:
            ph_sif_core = f"{PH_NODE_DIR_PROCESSOR_SIFS}/{sif_ocrd_all}"
        nf_run_command = self.cmd_nextflow_run(
            hpc_nf_script_path=hpc_nf_script_path, hpc_ws_dir=hpc_workspace_dir,
            bind_ocrd_models=f"{PH_NODE_DIR_OCRD_MODELS}/ocrd-resources:/usr/local/share/ocrd-resources",
            sif_core=sif_ocrd_core,
            sif_ocrd_all=sif_ocrd_all, input_file_grp=input_file_grp, mets_basename=mets_basename,
            use_mets_server=use_mets_server, nf_executable_steps=nf_executable_steps, ws_pages_amount=ws_pages_amount,
            cpus=cpus, ram=ram, forks=nf_process_forks, use_slim_images=HPC_USE_SLIM_IMAGES
        )

        if HPC_USE_SLIM_IMAGES:
            ocrd_processor_images = ",".join([OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE[exe] for exe in nf_executable_steps])
            ocrd_processor_images = f"{sif_ocrd_core},{ocrd_processor_images}"
        else:
            ocrd_processor_images = sif_ocrd_all
        regular_args = {
            "project_base_dir": self.project_root_dir,
            "scratch_base_dir": self.slurm_workspaces_dir,
            "ocrd_processor_images": ocrd_processor_images,
            "workflow_job_id": workflow_job_id,
            "workspace_id": workspace_id,
            "use_mets_server_bash_flag": use_mets_server_bash_flag,
            "file_groups_to_remove": file_groups_to_remove,
            "hpc_workflow_job_dir": hpc_workflow_job_dir,
            "hpc_workspace_dir": hpc_workspace_dir,
            "nf_run_command": nf_run_command,
            "print_ocrd_version_command": self.cmd_core_print_version(hpc_workspace_dir, ph_sif_core),
            "start_mets_server_command": self.cmd_core_start_mets_server(hpc_workspace_dir, ph_sif_core),
            "stop_mets_server_command": self.cmd_core_stop_mets_server(hpc_workspace_dir, ph_sif_core),
            "list_file_groups_command": self.cmd_core_list_file_groups(hpc_workspace_dir, ph_sif_core),
            "remove_file_group_command": self.cmd_core_remove_file_group(hpc_workspace_dir, ph_sif_core)
        }
        command += f" '{dumps(sbatch_args)}' '{dumps(regular_args)}'"

        self.logger.info(f"About to execute a force command: {command}")
        output, err, return_code = self.execute_blocking(command)
        self.logger.info(f"Command output: {output}")
        self.logger.info(f"Command err: {err}")
        self.logger.info(f"Command return code: {return_code}")
        slurm_job_id = output[0].strip('\n').split(' ')[-1]
        self.logger.info(f"Slurm job id: {slurm_job_id}")
        assert int(slurm_job_id)
        return slurm_job_id

    def check_slurm_job_state(
        self, slurm_job_id: str, tries: int = CHECK_SLURM_JOB_TRY_TIMES, wait_time: int = CHECK_SLURM_JOB_WAIT_TIME
    ) -> str:
        command = f"{HPC_WRAPPER_CHECK_WORKFLOW_JOB_STATUS} {slurm_job_id}"
        slurm_job_state = None

        while not slurm_job_state and tries > 0:
            self.logger.info(f"About to execute a force command: {command}")
            output, err, return_code = self.execute_blocking(command)
            self.logger.info(f"Command output: {output}")
            self.logger.info(f"Command err: {err}")
            self.logger.info(f"Command return code: {return_code}")
            if output:
                if len(output) < 3:
                    self.logger.warning("The output has returned with less than 3 lines. "
                                        "The job has not been listed yet.")
                    continue
                # Split the last line and get the second element,
                # i.e., the state element in the requested output format
                slurm_job_state = output[-2].split()[1]
                # TODO: dirty fast fix, improve this
                if slurm_job_state.startswith('---'):
                    self.logger.warning("The output is dashes. The job has not been listed yet.")
                    slurm_job_state = None
                    continue
            if slurm_job_state:
                break
            tries -= 1
            sleep(wait_time)
        if not slurm_job_state:
            self.logger.warning(f"Returning a None slurm job state")
        self.logger.info(f"Slurm job state of {slurm_job_id}: {slurm_job_state}")
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
            if not slurm_job_state:
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
            # Sometimes the slurm state is still
            # not initialized inside the HPC environment.
            # This is not a problem that requires a raise of Exception
            self.logger.warning(f"Invalid SLURM job state: {slurm_job_state}")

        # Timeout reached
        self.logger.warning("Polling slurm job status timeout reached")
        return False

    @staticmethod
    def cmd_nextflow_run(
        hpc_nf_script_path: str, hpc_ws_dir: str, bind_ocrd_models: str, sif_core: str, sif_ocrd_all: str,
        input_file_grp: str, mets_basename: str, use_mets_server: bool, nf_executable_steps: List[str],
        ws_pages_amount: int, cpus: int, ram: int, forks: int, use_slim_images: bool
    ) -> str:
        nf_run_command = f"nextflow run {hpc_nf_script_path} -ansi-log false -with-report -with-trace"
        nf_run_command += f" --input_file_group {input_file_grp}"
        nf_run_command += f" --mets_path /ws_data/{mets_basename}"
        if use_mets_server:
            nf_run_command += f" --mets_socket_path /ws_data/mets_server.sock"
        nf_run_command += f" --workspace_dir /ws_data"
        nf_run_command += f" --pages {ws_pages_amount}"

        sif_images = [OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE[exe] for exe in nf_executable_steps]
        apptainer_cmd = f"apptainer exec --bind {hpc_ws_dir}:/ws_data --bind {bind_ocrd_models}"
        # Mets caching is disabled for the core, to avoid the cache error
        # when mergin mets files https://github.com/OCR-D/core/issues/1297
        apptainer_cmd_core = f"{apptainer_cmd} --env OCRD_METS_CACHING=false"
        apptainer_cmd_step = f"{apptainer_cmd} --env OCRD_METS_CACHING=true"
        apptainer_image = sif_core if use_slim_images else sif_ocrd_all
        core_command = f"{apptainer_cmd_core} {PH_NODE_DIR_PROCESSOR_SIFS}/{apptainer_image}"
        nf_run_command += f" --env_wrapper_cmd_core {PH_CMD_WRAPPER}{core_command}{PH_CMD_WRAPPER}"

        index = 0
        for sif_image in sif_images:
            apptainer_image = sif_image if use_slim_images else sif_ocrd_all
            step_command = f"{apptainer_cmd_step} {PH_NODE_DIR_PROCESSOR_SIFS}/{apptainer_image}"
            nf_run_command += f" --env_wrapper_cmd_step{index} {PH_CMD_WRAPPER}{step_command}{PH_CMD_WRAPPER}"
            index += 1
        nf_run_command += f" --cpus {cpus}"
        nf_run_command += f" --ram {ram}"
        nf_run_command += f" --forks {forks}"
        return nf_run_command

    @staticmethod
    def cmd_core_print_version(hpc_ws_dir: str, ph_sif_core: str) -> str:
        return f"apptainer exec --bind {hpc_ws_dir}:/ws_data {ph_sif_core} ocrd --version"

    @staticmethod
    def cmd_core_start_mets_server(hpc_ws_dir: str, ph_sif_core: str) -> str:
        command = f"apptainer exec --bind {hpc_ws_dir}:/ws_data {ph_sif_core}"
        command += f" ocrd workspace -d /ws_data -U /ws_data/mets_server.sock server start"
        command += f" > {hpc_ws_dir}/mets_server.log 2>&1 &"
        return command

    @staticmethod
    def cmd_core_stop_mets_server(hpc_ws_dir: str, ph_sif_core: str) -> str:
        command = f"apptainer exec --bind {hpc_ws_dir}:/ws_data {ph_sif_core}"
        command += " ocrd workspace -d /ws_data -U /ws_data/mets_server.sock server stop"
        return command

    @staticmethod
    def cmd_core_list_file_groups(hpc_ws_dir: str, ph_sif_core: str) -> str:
        command = f"apptainer exec --bind {hpc_ws_dir}:/ws_data {ph_sif_core}"
        command += " ocrd workspace -d /ws_data list-group"
        return command

    @staticmethod
    def cmd_core_remove_file_group(hpc_ws_dir: str, ph_sif_core: str) -> str:
        command = f"apptainer exec --bind {hpc_ws_dir}:/ws_data {ph_sif_core}"
        command += " ocrd workspace -d /ws_data remove-group -r -f FILE_GROUP_PLACEHOLDER"
        command += f" > {hpc_ws_dir}/remove_file_groups.log 2>&1"
        return command
