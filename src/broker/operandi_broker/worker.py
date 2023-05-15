import json
import logging
import signal
from os import getppid, setsid
from sys import exit

import ocrd_webapi.database as db

from operandi_utils import reconfigure_all_loggers
from operandi_utils.hpc import HPCExecutor, HPCIOTransfer
from operandi_utils.rabbitmq import RMQConsumer

from .constants import (
    LOG_LEVEL_WORKER,
    LOG_FILE_PATH_WORKER_PREFIX
)


# Each worker class listens to a specific queue,
# consume messages, and process messages.
class Worker:
    def __init__(self, db_url, rmq_host, rmq_port, rmq_vhost, rmq_username, rmq_password, queue_name):
        self.log = logging.getLogger(__name__)
        self.queue_name = queue_name
        self.log_file_path = f"{LOG_FILE_PATH_WORKER_PREFIX}_{queue_name}.log"

        self.db_url = db_url
        # Connection to RabbitMQ related parameters
        self.rmq_host = rmq_host
        self.rmq_port = rmq_port
        self.rmq_vhost = rmq_vhost
        self.rmq_username = rmq_username
        self.rmq_password = rmq_password
        self.rmq_consumer = None

        self.hpc_executor = None
        self.hpc_io_transfer = None

        # Currently consumed message related parameters
        self.current_message_delivery_tag = None
        self.current_message_ws_id = None
        self.current_message_wf_id = None
        self.current_message_job_id = None
        self.has_consumed_message = False

    def run(self):
        try:
            # Source: https://unix.stackexchange.com/questions/18166/what-are-session-leaders-in-ps
            # Make the current process session leader
            setsid()
            # Reconfigure all loggers to the same format
            reconfigure_all_loggers(
                log_level=LOG_LEVEL_WORKER,
                log_file_path=self.log_file_path
            )
            self.log.info(f"Activating signal handler for SIGINT, SIGTERM")
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            db.sync_initiate_database(self.db_url)

            # Connect the HPC Executor
            self.hpc_executor = HPCExecutor()
            if self.hpc_executor:
                self.hpc_executor.connect()
                self.log.info("HPC executor connection successful.")
            else:
                self.log.error("HPC executor connection has failed.")

            # Connect the HPC IO Transfer
            self.hpc_io_transfer = HPCIOTransfer()
            if self.hpc_io_transfer:
                self.hpc_io_transfer.connect()
                self.log.info("HPC transfer connection successful.")
            else:
                self.log.error("HPC transfer connection has failed.")
            self.log.info("Worker runs jobs in HPC.")

            self.connect_consumer()
            self.configure_consuming(self.queue_name, self.__on_message_consumed_callback_hpc)

            self.start_consuming()
        except Exception as e:
            self.log.error(f"The worker failed to run, reason: {e}")
            raise Exception(f"The worker failed to run, reason: {e}")

    def connect_consumer(self):
        if self.rmq_consumer:
            # If for some reason connect_consumer() is called more than once.
            self.log.warning(f"The RMQConsumer was already instantiated. "
                             f"Overwriting the existing RMQConsumer.")
        self.log.info(f"Connecting RMQConsumer to RabbitMQ server: "
                      f"{self.rmq_host}:{self.rmq_port}{self.rmq_vhost}")
        self.rmq_consumer = RMQConsumer(host=self.rmq_host, port=self.rmq_port, vhost=self.rmq_vhost)
        # TODO: Remove this information before the release
        self.log.debug(f"RMQConsumer authenticates with username: "
                       f"{self.rmq_username}, password: {self.rmq_password}")
        self.rmq_consumer.authenticate_and_connect(username=self.rmq_username, password=self.rmq_password)
        self.log.info(f"Successfully connected RMQConsumer.")

    def configure_consuming(self, queue_name, callback_method):
        if not self.rmq_consumer:
            raise Exception("The RMQConsumer connection is not configured or broken")
        self.log.info(f"Configuring the consuming for queue: {queue_name}")
        self.rmq_consumer.configure_consuming(
            queue_name=queue_name,
            callback_method=callback_method
        )

    def start_consuming(self):
        if not self.rmq_consumer:
            raise Exception("The RMQConsumer connection is not configured or broken")
        self.log.info(f"Starting consuming from queue: {self.queue_name}")
        self.rmq_consumer.start_consuming()

    # TODO: Remove, currently left for reference
    """
    # The callback method provided to the Consumer listener
    # The arguments to this method are passed by the caller
    def __on_message_consumed_callback(self, ch, method, properties, body):
        # self.log.debug(f"ch: {ch}, method: {method}, properties: {properties}, body: {body}")
        # self.log.debug(f"Consumed message: {body}")

        self.current_message_delivery_tag = method.delivery_tag
        self.has_consumed_message = True

        # Since the workflow_message is constructed by the Operandi Server,
        # it should not fail here when parsing under normal circumstances.
        try:
            consumed_message = json.loads(body)
            self.log.info(f"Consumed message: {consumed_message}")
            self.current_message_ws_id = consumed_message["workspace_id"]
            self.current_message_wf_id = consumed_message["workflow_id"]
            self.current_message_job_id = consumed_message["job_id"]
            input_file_grp = consumed_message["input_file_grp"]
        except Exception as error:
            self.log.error(f"Parsing the consumed message has failed: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # Handle database related reads and set the workflow job status to RUNNING
        try:
            # TODO: This should be optimized, i.e., single read to the DB instead of three
            workflow_script_path = db.sync_get_workflow_script_path(self.current_message_wf_id)
            workspace_mets_path = db.sync_get_workspace_mets_path(self.current_message_ws_id)
            workspace_path = db.sync_get_workspace(self.current_message_ws_id).workspace_path
            job_dir = db.sync_get_workflow_job(self.current_message_job_id).job_path
            job_state = "RUNNING"
            self.log.info(f"Setting new job state[{job_state}] of job_id: {self.current_message_job_id}")
            db.sync_set_workflow_job_state(self.current_message_job_id, job_state=job_state)
        except Exception as error:
            self.log.error(f"Database related error has occurred: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # Trigger a Nextflow process
        try:
            nf_process = NextflowManager.execute_workflow(
                workspace_mets_path=workspace_mets_path,
                workspace_path=workspace_path,
                job_dir=job_dir,
                in_background=False,
                nf_script_path=workflow_script_path
            )
        except Exception as error:
            self.log.error(f"Triggering a nextflow process has failed: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # The worker blocks here till the nextflow process finishes

        if nf_process.returncode != 0:
            self.log.error(f"The Nextflow process exited with return code: {nf_process.returncode}")
            self.__handle_message_failure(interruption=False)
            return

        self.log.debug(f"The Nextflow process has finished successfully")
        job_state = "SUCCESS"
        self.log.info(f"Setting new state[{job_state}] of job_id: {self.current_message_job_id}")
        db.sync_set_workflow_job_state(self.current_message_job_id, job_state=job_state)
        self.has_consumed_message = False
        self.log.debug(f"Acking delivery tag: {self.current_message_delivery_tag}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        """

    def __on_message_consumed_callback_hpc(self, ch, method, properties, body):
        # self.log.debug(f"ch: {ch}, method: {method}, properties: {properties}, body: {body}")
        # self.log.debug(f"Consumed message: {body}")

        self.current_message_delivery_tag = method.delivery_tag
        self.has_consumed_message = True

        # Since the workflow_message is constructed by the Operandi Server,
        # it should not fail here when parsing under normal circumstances.
        try:
            consumed_message = json.loads(body)
            self.log.info(f"Consumed message: {consumed_message}")
            self.current_message_ws_id = consumed_message["workspace_id"]
            self.current_message_wf_id = consumed_message["workflow_id"]
            self.current_message_job_id = consumed_message["job_id"]
            input_file_grp = consumed_message["input_file_grp"]
        except Exception as error:
            self.log.error(f"Parsing the consumed message has failed: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # Handle database related reads and set the workflow job status to RUNNING
        try:
            # TODO: This should be optimized, i.e., single read to the DB instead of three
            workflow_script_path = db.sync_get_workflow_script_path(self.current_message_wf_id)
            workspace_mets_path = db.sync_get_workspace_mets_path(self.current_message_ws_id)
            workspace_path = db.sync_get_workspace(self.current_message_ws_id).workspace_path
            job_dir = db.sync_get_workflow_job(self.current_message_job_id).job_path
            job_state = "RUNNING"
            self.log.info(f"Setting new job state[{job_state}] of job_id: {self.current_message_job_id}")
            db.sync_set_workflow_job_state(self.current_message_job_id, job_state=job_state)
        except Exception as error:
            self.log.error(f"Database related error has occurred: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # Trigger a slurm job in the HPC
        try:
            # TODO: Use the actual nextflow workflow script here,
            #  instead of using the nextflow_workflows/template_workflow.nf
            slurm_job_return_code = self.prepare_and_trigger_slurm_job(
                workspace_id=self.current_message_ws_id,
                workspace_dir=workspace_path,
                workflow_job_id=self.current_message_job_id,
                workflow_job_dir=job_dir,
                input_file_grp=input_file_grp,
                nf_workflow_script=workflow_script_path,
            )
        except Exception as error:
            self.log.error(f"Triggering a slurm job in the HPC has failed: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # TODO: The worker blocks here till the slurm job finishes
        # TODO: Continuously check slurm job status here

        if slurm_job_return_code != 0:
            self.log.error(f"The slurm job failed for job_id: {self.current_message_job_id}")
            self.__handle_message_failure(interruption=False)
            return

        self.log.debug(f"The Nextflow process has finished successfully")
        job_state = "SUCCESS"
        self.log.info(f"Setting new state[{job_state}] of job_id: {self.current_message_job_id}")
        db.sync_set_workflow_job_state(self.current_message_job_id, job_state=job_state)
        self.has_consumed_message = False
        self.log.debug(f"Acking delivery tag: {self.current_message_delivery_tag}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __handle_message_failure(self, interruption: bool = False):
        job_state = "STOPPED"
        self.log.info(f"Setting new state[{job_state}] of job_id: {self.current_message_job_id}")
        db.sync_set_workflow_job_state(
            job_id=self.current_message_job_id,
            job_state=job_state
        )
        self.has_consumed_message = False

        if interruption:
            # self.log.debug(f"Nacking delivery tag: {self.current_message_delivery_tag}")
            # self.rmq_consumer._channel.basic_nack(delivery_tag=self.current_message_delivery_tag)
            # TODO: Sending ACK for now because it is hard to clean up without a mets workspace backup mechanism
            self.log.debug(f"Interruption Acking delivery tag: {self.current_message_delivery_tag}")
            self.rmq_consumer._channel.basic_ack(delivery_tag=self.current_message_delivery_tag)
            return

        self.log.debug(f"Acking delivery tag: {self.current_message_delivery_tag}")
        self.rmq_consumer._channel.basic_ack(delivery_tag=self.current_message_delivery_tag)

        # Reset the current message related parameters
        self.current_message_delivery_tag = None
        self.current_message_ws_id = None
        self.current_message_wf_id = None
        self.current_message_job_id = None

    # TODO: Ideally this method should be wrapped to be able
    #  to pass internal data from the Worker class required for the cleaning
    # The arguments to this method are passed by the caller from the OS
    def signal_handler(self, sig, frame):
        signal_name = signal.Signals(sig).name
        self.log.info(f"{signal_name} received from parent process[{getppid()}].")
        if self.has_consumed_message:
            self.log.info(f"Handling the message failure due to interruption: {signal_name}")
            self.__handle_message_failure(interruption=True)

        # TODO: Disconnect the RMQConsumer properly
        # TODO: Clean the remaining leftovers (if any)
        self.rmq_consumer._channel.close()
        self.rmq_consumer = None
        self.log.info("Exiting gracefully.")
        exit(0)

    # TODO: This should be further refined, currently it's just everything in one place
    def prepare_and_trigger_slurm_job(
            self,
            workspace_id,
            workspace_dir,
            workflow_job_id,
            workflow_job_dir,
            input_file_grp,
            nf_workflow_script=None
    ) -> int:
        hpc_batch_script_path = self.hpc_io_transfer.put_batch_script(
            batch_script_id="submit_workflow_job.sh"
        )

        hpc_slurm_workspace_path, nextflow_script_id = self.hpc_io_transfer.put_slurm_workspace(
            ocrd_workspace_id=workspace_id,
            ocrd_workspace_dir=workspace_dir,
            workflow_job_id=workflow_job_id,
            nextflow_script_path=nf_workflow_script      
        )

        # NOTE: The paths below must be a valid existing path inside the HPC
        slurm_job_id = self.hpc_executor.trigger_slurm_job(
            batch_script_path=hpc_batch_script_path,
            workflow_job_id=workflow_job_id,
            nextflow_script_id=nextflow_script_id,
            input_file_grp=input_file_grp,
            workspace_id=workspace_id
        )

        finished_successfully = self.hpc_executor.poll_till_end_slurm_job_state(
            slurm_job_id=slurm_job_id,
            interval=10,
            timeout=1800  # seconds, i.e., 30 minutes
        )

        if finished_successfully:
            self.hpc_io_transfer.get_slurm_workspace(
                ocrd_workspace_id=workspace_id,
                ocrd_workspace_dir=workspace_dir,
                hpc_slurm_workspace_path=hpc_slurm_workspace_path,
                workflow_job_dir=workflow_job_dir,
            )
            # Delete the result dir from the HPC home folder
            self.hpc_executor.execute_blocking(f"bash -lc 'rm -rf {hpc_slurm_workspace_path}'")
        else:
            raise Exception(f"Slurm job has failed: {slurm_job_id}")
        return 0
