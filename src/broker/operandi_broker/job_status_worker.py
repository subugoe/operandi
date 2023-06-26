import json
import logging
import signal
from os import getppid, setsid
from sys import exit

from operandi_utils import reconfigure_all_loggers
import operandi_utils.database.database as db
from operandi_utils.hpc import HPCExecutor
from operandi_utils.rabbitmq import RMQConsumer

from .constants import (
    LOG_LEVEL_WORKER,
    LOG_FILE_PATH_WORKER_PREFIX
)


class JobStatusWorker:
    def __init__(self, db_url, rmq_host, rmq_port, rmq_vhost, rmq_username, rmq_password, queue_name, test_sbatch=False):
        self.log = logging.getLogger(__name__)
        self.queue_name = queue_name
        self.log_file_path = f"{LOG_FILE_PATH_WORKER_PREFIX}_{queue_name}.log"
        self.test_sbatch = test_sbatch

        self.db_url = db_url
        # Connection to RabbitMQ related parameters
        self.rmq_host = rmq_host
        self.rmq_port = rmq_port
        self.rmq_vhost = rmq_vhost
        self.rmq_username = rmq_username
        self.rmq_password = rmq_password
        self.rmq_consumer = None

        self.hpc_executor = None

        # Currently consumed message related parameters
        self.current_message_delivery_tag = None
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

    def __on_message_consumed_callback_hpc(self, ch, method, properties, body):
        self.log.debug(f"ch: {ch}, method: {method}, properties: {properties}, body: {body}")
        self.log.debug(f"Consumed message: {body}")

        self.current_message_delivery_tag = method.delivery_tag
        self.has_consumed_message = True

        # Since the workflow_message is constructed by the Operandi Server,
        # it should not fail here when parsing under normal circumstances.
        try:
            consumed_message = json.loads(body)
            self.log.info(f"Consumed message: {consumed_message}")
            self.current_message_job_id = consumed_message["job_id"]
        except Exception as error:
            self.log.error(f"Parsing the consumed message has failed: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # Handle database related reads and set the workflow job status to RUNNING
        try:
            # TODO: This should be optimized, i.e., single read to the DB instead of three
            workflow_job_db = db.sync_get_workflow_job(self.current_message_job_id)
            hpc_slurm_job_db = db.sync_get_hpc_slurm_job(self.current_message_job_id)
        except Exception as error:
            self.log.error(f"Database related error has occurred: {error}")
            self.__handle_message_failure(interruption=False)
            return

        if workflow_job_db:
            slurm_job_id = hpc_slurm_job_db.hpc_slurm_job_id
            if not slurm_job_id:
                self.log.warning(f"slurm_job_id is: {slurm_job_id}")
            slurm_job_state = self.hpc_executor.check_slurm_job_state(slurm_job_id=slurm_job_id)
            if not slurm_job_state:
                self.log.warning(f"slurm_job_id: {slurm_job_id}, slurm job state is: {slurm_job_state}")
            else:
                self.log.info(f"Slurm job state is: {slurm_job_state}")

            # TODO: This duplication is the same as in executor.py
            #  Refactor it when things are working
            slurm_fail_states = ["BOOT_FAIL", "CANCELLED", "DEADLINE", "FAILED", "NODE_FAIL",
                                 "OUT_OF_MEMORY", "PREEMPTED", "REVOKED", "TIMEOUT"]
            slurm_success_states = ["COMPLETED"]
            slurm_waiting_states = ["RUNNING", "PENDING", "COMPLETING", "REQUEUED", "RESIZING", "SUSPENDED"]

            # Take the latest workflow job state
            workflow_job_status = workflow_job_db.job_state
            if slurm_job_state in slurm_success_states:
                workflow_job_status = "SUCCESS"
            if slurm_job_state in slurm_waiting_states:
                workflow_job_status = "RUNNING"
            if slurm_job_state in slurm_fail_states:
                workflow_job_status = "STOPPED"

            self.log.info(f"Setting workflow job state to: {workflow_job_status}")
            db.sync_set_workflow_job_state(self.current_message_job_id, job_state=workflow_job_status)
        else:
            self.log.warning(f"Workflow job not existing in DB: {self.current_message_job_id}")

        self.has_consumed_message = False
        self.log.debug(f"Acking delivery tag: {self.current_message_delivery_tag}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __handle_message_failure(self, interruption: bool = False):
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
