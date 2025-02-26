from json import loads
from os.path import join
from pathlib import Path
from typing import List
from typing_extensions import override

from operandi_broker.job_worker_base import JobWorkerBase

from operandi_utils.constants import StateJob, StateWorkspace
from operandi_utils.database import (
    DBWorkflow, DBWorkflowJob, DBWorkspace,
    sync_db_increase_processing_stats, sync_db_get_workflow, sync_db_get_workflow_job, sync_db_get_workspace,
    sync_db_create_hpc_slurm_job, sync_db_update_workflow_job, sync_db_update_workspace)
from operandi_utils.hpc.constants import (
    HPC_BATCH_SUBMIT_WORKFLOW_JOB, HPC_JOB_DEADLINE_TIME_REGULAR, HPC_JOB_DEADLINE_TIME_TEST, HPC_JOB_QOS_SHORT,
    HPC_JOB_QOS_DEFAULT)


class JobWorkerSubmit(JobWorkerBase):
    def __init__(self, db_url, rabbitmq_url, queue_name, test_sbatch=False):
        super().__init__(db_url, rabbitmq_url, queue_name)
        self.test_sbatch = test_sbatch
        self.current_message_job_id = None
        self.current_message_user_id = None
        self.current_message_wf_id = None
        self.current_message_ws_id = None

    @override
    def _consumed_msg_callback(self, ch, method, properties, body):
        self.log.debug(f"ch: {ch}, method: {method}, properties: {properties}, body: {body}")
        self.log.debug(f"Consumed message: {body}")
        self.current_message_delivery_tag = method.delivery_tag
        self.has_consumed_message = True

        # Since the workflow_message is constructed by the Operandi Server,
        # it should not fail here when parsing under normal circumstances.
        try:
            consumed_message = loads(body)
            self.log.info(f"Consumed message: {consumed_message}")
            self.current_message_job_id = consumed_message["job_id"]
            input_file_grp = consumed_message["input_file_grp"]
            remove_file_grps = consumed_message["remove_file_grps"]
            slurm_job_partition = consumed_message["partition"]
            slurm_job_cpus = int(consumed_message["cpus"])
            slurm_job_ram = int(consumed_message["ram"])
            # How many process instances to create for each OCR-D processor
            # By default, the amount of cpus, since that gives optimal performance
            nf_process_forks = slurm_job_cpus
        except Exception as error:
            self.log.error(f"Parsing the consumed message has failed: {error}")
            self._handle_msg_failure(interruption=False)
            return

        try:
            db_workflow_job: DBWorkflowJob = sync_db_get_workflow_job(self.current_message_job_id)
            self.current_message_user_id = db_workflow_job.user_id
            self.current_message_wf_id = db_workflow_job.workflow_id
            self.current_message_ws_id = db_workflow_job.workspace_id

            db_workflow: DBWorkflow = sync_db_get_workflow(self.current_message_wf_id)
            workflow_script_path = Path(db_workflow.workflow_script_path)
            nf_uses_mets_server = db_workflow.uses_mets_server
            nf_executable_steps = db_workflow.executable_steps

            db_workspace: DBWorkspace = sync_db_get_workspace(self.current_message_ws_id)
            workspace_dir = Path(db_workspace.workspace_dir)
            mets_basename = db_workspace.mets_basename
            ws_pages_amount = db_workspace.pages_amount
            if not mets_basename:
                mets_basename = "mets.xml"
        except RuntimeError as error:
            self.log.error(f"Database run-time error has occurred: {error}")
            self._handle_msg_failure(interruption=False)
            return
        except Exception as error:
            self.log.error(f"Database related error has occurred: {error}")
            self._handle_msg_failure(interruption=False)
            return

        # Trigger a slurm job in the HPC
        try:
            self.prepare_and_trigger_slurm_job(
                workflow_job_id=self.current_message_job_id, workspace_id=self.current_message_ws_id,
                workspace_dir=workspace_dir, workspace_base_mets=mets_basename,
                workflow_script_path=workflow_script_path, input_file_grp=input_file_grp,
                nf_process_forks=nf_process_forks, ws_pages_amount=ws_pages_amount, use_mets_server=nf_uses_mets_server,
                nf_executable_steps=nf_executable_steps, file_groups_to_remove=remove_file_grps, cpus=slurm_job_cpus,
                ram=slurm_job_ram, partition=slurm_job_partition
            )

            job_state = StateJob.PENDING
            self.log.info(f"Setting new job state `{job_state}` of job_id: {self.current_message_job_id}")
            sync_db_update_workflow_job(find_job_id=self.current_message_job_id, job_state=job_state)

            ws_state = StateWorkspace.PENDING
            self.log.info(f"Setting new workspace state `{ws_state}` of workspace_id: {self.current_message_ws_id}")
            sync_db_update_workspace(find_workspace_id=self.current_message_ws_id, state=ws_state)

            self.log.info(f"The HPC slurm job was successfully submitted")
        except Exception as error:
            self.log.error(f"Triggering a slurm job in the HPC has failed: {error}")
            self._handle_msg_failure(interruption=False)
            return

        self.has_consumed_message = False
        self.log.debug(f"Ack delivery tag: {self.current_message_delivery_tag}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    @override
    def _handle_msg_failure(self, interruption: bool):
        job_state = StateJob.FAILED
        self.log.info(f"Setting new state `{job_state}` of job_id: {self.current_message_job_id}")
        sync_db_update_workflow_job(find_job_id=self.current_message_job_id, job_state=job_state)
        self.has_consumed_message = False

        ws_state = StateWorkspace.READY
        self.log.info(f"Setting new workspace state `{ws_state}` of workspace_id: {self.current_message_ws_id}")
        sync_db_update_workspace(find_workspace_id=self.current_message_ws_id, state=ws_state)

        if interruption:
            # self.log.info(f"Nacking delivery tag: {self.current_message_delivery_tag}")
            # self.rmq_consumer._channel.basic_nack(delivery_tag=self.current_message_delivery_tag)
            # TODO: Sending ACK for now because it is hard to clean up without a mets workspace backup mechanism
            self.log.info(f"Interruption Ack delivery tag: {self.current_message_delivery_tag}")
            self.rmq_consumer.ack_message(delivery_tag=self.current_message_delivery_tag)
            return

        self.log.debug(f"Ack delivery tag: {self.current_message_delivery_tag}")
        self.rmq_consumer.ack_message(delivery_tag=self.current_message_delivery_tag)

        # Reset the current message related parameters
        self.current_message_delivery_tag = None
        self.current_message_job_id = None
        self.current_message_user_id = None
        self.current_message_wf_id = None
        self.current_message_ws_id = None

    # TODO: This should be further refined, currently it's just everything in one place
    def prepare_and_trigger_slurm_job(
        self, workflow_job_id: str, workspace_id: str, workspace_dir: Path, workspace_base_mets: str,
        workflow_script_path: Path, input_file_grp: str, nf_process_forks: int, ws_pages_amount: int,
        use_mets_server: bool, nf_executable_steps: List[str], file_groups_to_remove: str, cpus: int, ram: int,
        partition: str
    ) -> str:
        if self.test_sbatch:
            job_deadline_time = HPC_JOB_DEADLINE_TIME_TEST
            qos = HPC_JOB_QOS_SHORT
        else:
            job_deadline_time = HPC_JOB_DEADLINE_TIME_REGULAR
            qos = HPC_JOB_QOS_DEFAULT

        # Recreate the transfer connection for each workflow job submission
        # This is required due to all kind of nasty connection fails - timeouts,
        # paramiko transport not reporting properly, etc.
        # self.hpc_executor = HPCExecutor(tunel_host='localhost', tunel_port=4022)
        # self.log.info("HPC executor connection renewed successfully.")
        # self.hpc_io_transfer = HPCTransfer(tunel_host='localhost', tunel_port=4023)
        # self.log.info("HPC transfer connection renewed successfully.")

        try:
            sync_db_update_workspace(find_workspace_id=workspace_id, state=StateWorkspace.TRANSFERRING_TO_HPC)
            sync_db_update_workflow_job(find_job_id=workflow_job_id, job_state=StateJob.TRANSFERRING_TO_HPC)
            self.hpc_io_transfer.pack_and_put_slurm_workspace(
                ocrd_workspace_dir=workspace_dir, workflow_job_id=workflow_job_id,
                nextflow_script_path=workflow_script_path)
        except Exception as error:
            raise Exception(f"Failed to pack and put slurm workspace: {error}")

        try:
            # NOTE: The paths below must be a valid existing path inside the HPC
            slurm_job_id = self.hpc_executor.trigger_slurm_job(
                workflow_job_id=workflow_job_id, nextflow_script_path=workflow_script_path,
                workspace_id=workspace_id, mets_basename=workspace_base_mets,
                input_file_grp=input_file_grp, nf_process_forks=nf_process_forks, ws_pages_amount=ws_pages_amount,
                use_mets_server=use_mets_server, nf_executable_steps=nf_executable_steps,
                file_groups_to_remove=file_groups_to_remove, cpus=cpus, ram=ram, job_deadline_time=job_deadline_time,
                partition=partition, qos=qos)
        except Exception as error:
            db_stats = sync_db_increase_processing_stats(
                find_user_id=self.current_message_user_id, pages_failed=ws_pages_amount)
            self.log.error(f"Increasing `pages_failed` stat by {ws_pages_amount}")
            self.log.error(f"Total amount of `pages_failed` stat: {db_stats.pages_failed}")
            raise Exception(f"Triggering slurm job failed: {error}")

        try:
            sync_db_create_hpc_slurm_job(
                user_id=self.current_message_user_id,
                workflow_job_id=workflow_job_id, hpc_slurm_job_id=slurm_job_id,
                hpc_batch_script_path=HPC_BATCH_SUBMIT_WORKFLOW_JOB,
                hpc_slurm_workspace_path=join(self.hpc_io_transfer.slurm_workspaces_dir, workflow_job_id))
        except Exception as error:
            raise Exception(f"Failed to save the hpc slurm job in DB: {error}")
        return slurm_job_id
