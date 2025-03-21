from logging import getLogger
from os import environ
from time import sleep

from operandi_utils import (
    get_log_file_path_prefix, reconfigure_all_loggers, verify_database_uri, verify_and_parse_mq_uri)
from operandi_utils.constants import LOG_LEVEL_BROKER
from operandi_utils.hpc import NHRExecutor, NHRTransfer
from operandi_utils.rabbitmq.constants import (
    RABBITMQ_QUEUE_HPC_DOWNLOADS, RABBITMQ_QUEUE_HARVESTER, RABBITMQ_QUEUE_USERS, RABBITMQ_QUEUE_JOB_STATUSES)

from .broker_utils import create_child_process, kill_workers


class ServiceBroker:
    def __init__(
        self, db_url: str = environ.get("OPERANDI_DB_URL"), rabbitmq_url: str = environ.get("OPERANDI_RABBITMQ_URL"),
        test_sbatch: bool = False
    ):
        if not db_url:
            raise ValueError("Environment variable not set: OPERANDI_DB_URL")
        if not rabbitmq_url:
            raise ValueError("Environment variable not set: OPERANDI_RABBITMQ_URL")

        log_file_path = f"{get_log_file_path_prefix(module_type='broker')}.log"
        # Reconfigure all loggers to the same format
        reconfigure_all_loggers(log_level=LOG_LEVEL_BROKER, log_file_path=log_file_path)

        self.log = getLogger("operandi_broker.service_broker")
        self.test_sbatch = test_sbatch

        try:
            self.db_url = verify_database_uri(db_url)
            self.log.debug(f'Verified MongoDB URL: {db_url}')
            verify_and_parse_mq_uri(rabbitmq_url)
            self.rabbitmq_url = rabbitmq_url
            self.log.debug(f'Verified RabbitMQ URL: {rabbitmq_url}')
        except ValueError as e:
            raise ValueError(e)

        try:
            NHRTransfer().upload_batch_scripts()
            NHRExecutor().make_remote_batch_scripts_executable()
        except Exception as error:
            self.log.error(f"Error while trying to upload batch scripts to HPC: {error}")

        # A dictionary to keep track of queues and worker pids
        # Keys: Each key is a unique queue name
        # Value: List of worker pids consuming from the key queue name
        self.queues_and_workers = {}

    def run_broker(self):
        # A list of queues for which a worker process should be created
        queues = [RABBITMQ_QUEUE_HARVESTER, RABBITMQ_QUEUE_USERS]
        status_queue = RABBITMQ_QUEUE_JOB_STATUSES
        hpc_download_queue = RABBITMQ_QUEUE_HPC_DOWNLOADS

        try:
            for queue_name in queues:
                self.log.info(f"Creating a worker process to consume from queue: {queue_name}")
                self.create_worker_process(queue_name, "submit_worker")
            self.log.info(f"Creating a status worker process to consume from queue: {status_queue}")
            self.create_worker_process(status_queue, "status_worker")
            self.log.info(f"Creating a download worker process to consume from queue: {hpc_download_queue}")
            self.create_worker_process(hpc_download_queue, "download_worker")
        except Exception as error:
            self.log.error(f"Error while creating worker processes: {error}")

        try:
            # Sleep the parent process till a signal is invoked
            # Better than sleeping in loop, not tested yet
            # signal.pause()

            # Loop and sleep
            while True:
                sleep(5)
        # TODO: Check this in docker environment
        # This may not work with SSH/Docker, SIGINT may not be caught with KeyboardInterrupt.
        except KeyboardInterrupt:
            self.log.info(f"SIGINT signal received. Sending SIGINT to worker processes.")
            # Sends SIGINT to workers
            kill_workers(self.log, self.queues_and_workers)
            self.log.info(f"Closing gracefully in 3 seconds!")
            exit(0)
        except Exception as error:
            # This is for logging any other errors
            self.log.error(f"Unexpected error: {error}")

    # Creates a separate worker process and append its pid if successful
    def create_worker_process(self, queue_name, worker_type: str) -> None:
        # If the entry for queue_name does not exist, create id
        if queue_name not in self.queues_and_workers:
            self.log.info(f"Initializing workers list for queue: {queue_name}")
            # Initialize the worker pids list for the queue
            self.queues_and_workers[queue_name] = []
        child_pid = create_child_process(
            self.log, self.db_url, self.rabbitmq_url, queue_name, worker_type, self.test_sbatch)
        # If creation of the child process was successful
        if child_pid:
            self.log.info(f"Assigning a new worker process with pid: {child_pid}, to queue: {queue_name}")
            # append the pid to the workers list of the queue_name
            (self.queues_and_workers[queue_name]).append(child_pid)

    def kill_workers(self):
        kill_workers(self.log, self.queues_and_workers)
