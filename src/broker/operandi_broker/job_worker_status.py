from json import dumps, loads
from typing_extensions import override

from operandi_broker.job_worker_base import JobWorkerBase
from operandi_utils.constants import StateJob, StateWorkspace
from operandi_utils.database import (
    DBHPCSlurmJob, DBWorkflowJob,
    sync_db_get_hpc_slurm_job, sync_db_get_workflow_job,
    sync_db_update_hpc_slurm_job, sync_db_update_workflow_job, sync_db_update_workspace)
from operandi_utils.rabbitmq import RABBITMQ_QUEUE_HPC_DOWNLOADS


class JobWorkerStatus(JobWorkerBase):
    def __init__(self, db_url, rabbitmq_url, queue_name):
        super().__init__(db_url, rabbitmq_url, queue_name)
        self.current_message_job_id = None

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
        except Exception as error:
            self.log.warning(f"Parsing the consumed message has failed: {error}")
            self._handle_msg_failure(interruption=False)
            return

        try:
            db_hpc_slurm_job: DBHPCSlurmJob = sync_db_get_hpc_slurm_job(self.current_message_job_id)
            db_workflow_job: DBWorkflowJob = sync_db_get_workflow_job(self.current_message_job_id)
            workspace_id = db_workflow_job.workspace_id
        except RuntimeError as error:
            self.log.warning(f"Database run-time error has occurred: {error}")
            self._handle_msg_failure(interruption=False)
            return
        except Exception as error:
            self.log.warning(f"Database related error has occurred: {error}")
            self._handle_msg_failure(interruption=False)
            return

        try:
            self.__handle_hpc_and_workflow_states(
                db_hpc_slurm_job=db_hpc_slurm_job, db_workflow_job=db_workflow_job, workspace_id=workspace_id)
        except ValueError as error:
            self.log.warning(f"{error}")
            self._handle_msg_failure(interruption=False)
            return

        self.has_consumed_message = False
        self.log.debug(f"Ack delivery tag: {self.current_message_delivery_tag}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    @override
    def _handle_msg_failure(self, interruption: bool):
        self.has_consumed_message = False

        if interruption:
            # self.log.info(f"Nacking delivery tag: {self.current_message_delivery_tag}")
            # self.rmq_consumer._channel.basic_nack(delivery_tag=self.current_message_delivery_tag)
            # TODO: Sending ACK for now because it is hard to clean up without a mets workspace backup mechanism
            self.log.info(f"Interruption ack delivery tag: {self.current_message_delivery_tag}")
            self.rmq_consumer.ack_message(delivery_tag=self.current_message_delivery_tag)
            return

        self.log.debug(f"Ack delivery tag: {self.current_message_delivery_tag}")
        self.rmq_consumer.ack_message(delivery_tag=self.current_message_delivery_tag)

        # Reset the current message related parameters
        self.current_message_delivery_tag = None
        self.current_message_job_id = None

    def __handle_hpc_and_workflow_states(
        self, db_hpc_slurm_job: DBHPCSlurmJob, db_workflow_job: DBWorkflowJob, workspace_id: str
    ):
        old_slurm_job_state = db_hpc_slurm_job.hpc_slurm_job_state
        new_slurm_job_state = self.hpc_executor.check_slurm_job_state(slurm_job_id=db_hpc_slurm_job.hpc_slurm_job_id)

        if old_slurm_job_state == new_slurm_job_state:
            self.log.info(f"No change in slurm job state, state is still: {old_slurm_job_state}")
            return

        job_id = db_workflow_job.job_id
        old_job_state = db_workflow_job.job_state
        self.log.info(
            f"Job {db_hpc_slurm_job.hpc_slurm_job_id} changed state: {old_slurm_job_state} -> {new_slurm_job_state}")
        sync_db_update_hpc_slurm_job(find_workflow_job_id=job_id, hpc_slurm_job_state=new_slurm_job_state)

        # Convert the slurm job state to operandi workflow job state
        new_job_state = StateJob.convert_from_slurm_job(slurm_job_state=new_slurm_job_state)

        if old_job_state == new_job_state:
            self.log.info(f"No change in workflow job state needed, state is still: {old_job_state}")
            return

        if old_job_state in [StateJob.SUCCESS, StateJob.FAILED, StateJob.TRANSFERRING_FROM_HPC]:
            self.log.info(f"No change in workflow job state needed, state is already: {old_job_state}")
            return

        self.log.info(f"Workflow job: {job_id}, changed state: {old_job_state} -> {new_job_state}")
        sync_db_update_workflow_job(find_job_id=job_id, job_state=new_job_state)
        if new_job_state == StateJob.HPC_SUCCESS or new_job_state == StateJob.HPC_FAILED:
            sync_db_update_workspace(find_workspace_id=workspace_id, state=StateWorkspace.TRANSFERRING_FROM_HPC)
            sync_db_update_workflow_job(find_job_id=job_id, job_state=StateJob.TRANSFERRING_FROM_HPC)
            result_download_message = {"job_id": f"{job_id}", "previous_job_state": f"{new_job_state}"}
            self.log.info(f"Encoding the result download RabbitMQ message: {result_download_message}")
            encoded_result_download_message = dumps(result_download_message).encode(encoding="utf-8")
            self.rmq_publisher.publish_to_queue(
                queue_name=RABBITMQ_QUEUE_HPC_DOWNLOADS, message=encoded_result_download_message)

        self.log.info(f"Latest slurm job state: {new_slurm_job_state}")
        self.log.info(f"Latest workflow job state: {new_job_state}")
