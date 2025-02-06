from json import loads
from pathlib import Path
from typing import List
from typing_extensions import override

from ocrd import Resolver
from operandi_broker.job_worker_base import JobWorkerBase
from operandi_utils.constants import StateJob, StateWorkspace
from operandi_utils.database import (
    DBWorkspace, sync_db_increase_processing_stats,
    sync_db_get_hpc_slurm_job, sync_db_get_workflow_job, sync_db_get_workspace,
    sync_db_update_workflow_job, sync_db_update_workspace)


class JobWorkerDownload(JobWorkerBase):
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
            previous_job_state = consumed_message["previous_job_state"]
        except Exception as error:
            self.log.warning(f"Parsing the consumed message has failed: {error}")
            self._handle_msg_failure(interruption=False)
            return

        try:
            db_hpc_slurm_job = sync_db_get_hpc_slurm_job(self.current_message_job_id)
            slurm_job_id = db_hpc_slurm_job.hpc_slurm_job_id

            db_workflow_job = sync_db_get_workflow_job(self.current_message_job_id)
            workspace_id = db_workflow_job.workspace_id
            job_dir = db_workflow_job.job_dir

            db_workspace = sync_db_get_workspace(workspace_id)
            ws_dir = db_workspace.workspace_dir
            user_id = db_workspace.user_id
        except RuntimeError as error:
            self.log.warning(f"Database run-time error has occurred: {error}")
            self._handle_msg_failure(interruption=False)
            return
        except Exception as error:
            self.log.warning(f"Database related error has occurred: {error}")
            self._handle_msg_failure(interruption=False)
            return

        try:
            # TODO: Refactor this block of code since nothing is downloaded from the HPC when job fails.
            if previous_job_state == StateJob.HPC_SUCCESS:
                self.hpc_io_transfer.download_slurm_job_log_file(slurm_job_id, job_dir)
                self.__download_results_from_hpc(job_dir=job_dir, workspace_dir=ws_dir)
                self.log.info(f"Setting new workspace state `{StateWorkspace.READY}` of workspace_id: {workspace_id}")
                updated_file_groups = self.__extract_updated_file_groups(db_workspace=db_workspace)
                db_workspace = sync_db_update_workspace(
                    find_workspace_id=workspace_id, state=StateWorkspace.READY, file_groups=updated_file_groups)
                pages_amount = db_workspace.pages_amount
                self.log.info(f"Increasing `pages_succeed` stat by {pages_amount}")
                db_stats = sync_db_increase_processing_stats(find_user_id=user_id, pages_succeed=pages_amount)
                self.log.info(f"Total amount of `pages_succeed` stat: {db_stats.pages_succeed}")
                sync_db_update_workflow_job(find_job_id=self.current_message_job_id, job_state=StateJob.SUCCESS)
                self.log.info(f"Setting new workflow job state `{previous_job_state}`"
                              f" of job_id: {self.current_message_job_id}")
            if previous_job_state == StateJob.HPC_FAILED:
                self.hpc_io_transfer.download_slurm_job_log_file(slurm_job_id, job_dir)
                self.log.info(f"Setting new workspace state `{StateWorkspace.READY}` of workspace_id: {workspace_id}")
                db_workspace = sync_db_update_workspace(find_workspace_id=workspace_id, state=StateWorkspace.READY)
                pages_amount = db_workspace.pages_amount
                self.log.error(f"Increasing `pages_failed` stat by {pages_amount}")
                db_stats = sync_db_increase_processing_stats(find_user_id=user_id, pages_failed=pages_amount)
                self.log.error(f"Total amount of `pages_failed` stat: {db_stats.pages_failed}")
                sync_db_update_workflow_job(find_job_id=self.current_message_job_id, job_state=StateJob.FAILED)
                self.log.info(f"Setting new workflow job state `{previous_job_state}`"
                              f" of job_id: {self.current_message_job_id}")
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

    def __download_results_from_hpc(self, job_dir: str, workspace_dir: str) -> None:
        self.hpc_io_transfer.get_and_unpack_slurm_workspace(
            ocrd_workspace_dir=Path(workspace_dir), workflow_job_dir=Path(job_dir))
        self.log.info(f"Transferred slurm workspace from hpc path")
        # Delete the result dir from the HPC home folder
        job_id = Path(job_dir).name
        self.hpc_executor.remove_workflow_job_dir(workflow_job_id=job_id)
        self.log.info(f"Removed slurm workspace from HPC for job: {job_id}")

    def __extract_updated_file_groups(self, db_workspace: DBWorkspace) -> List[str]:
        try:
            workspace = Resolver().workspace_from_url(
                mets_url=db_workspace.workspace_mets_path, clobber_mets=False,
                mets_basename=db_workspace.mets_basename, download=False)
            return workspace.mets.file_groups
        except Exception as error:
            self.log.error(f"Failed to extract the processed file groups: {error}")
            return ["CORRUPTED FILE GROUPS"]
