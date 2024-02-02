from logging import getLogger
from os import environ, fork
import psutil
import signal
from time import sleep

from operandi_utils import (
    get_log_file_path_prefix,
    reconfigure_all_loggers,
    verify_database_uri,
    verify_and_parse_mq_uri
)
from operandi_utils.constants import LOG_LEVEL_BROKER
from operandi_utils.rabbitmq.constants import (
    RABBITMQ_QUEUE_HARVESTER,
    RABBITMQ_QUEUE_USERS,
    RABBITMQ_QUEUE_JOB_STATUSES
)
from .worker import Worker
from .job_status_worker import JobStatusWorker


class ServiceBroker:
    def __init__(
        self,
        db_url: str = environ.get("OPERANDI_DB_URL"),
        rabbitmq_url: str = environ.get("OPERANDI_RABBITMQ_URL"),
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

        # A dictionary to keep track of queues and worker pids
        # Keys: Each key is a unique queue name
        # Value: List of worker pids consuming from the key queue name
        self.queues_and_workers = {}

    def run_broker(self):
        # A list of queues for which a worker process should be created
        queues = [
            RABBITMQ_QUEUE_HARVESTER,
            RABBITMQ_QUEUE_USERS
        ]
        try:
            for queue_name in queues:
                self.log.info(f"Creating a worker processes to consume from queue: {queue_name}")
                self.create_worker_process(queue_name=queue_name, status_checker=False)
            self.log.info(
                f"Creating a status checker worker processes to consume from queue: {RABBITMQ_QUEUE_JOB_STATUSES}")
            self.create_worker_process(queue_name=RABBITMQ_QUEUE_JOB_STATUSES, status_checker=True)
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
            self.kill_workers()
            self.log.info(f"Closing gracefully in 3 seconds!")
            exit(0)
        except Exception as error:
            # This is for logging any other errors
            self.log.error(f"Unexpected error: {error}")

    # Creates a separate worker process and append its pid if successful
    def create_worker_process(self, queue_name, status_checker=False) -> None:
        # If the entry for queue_name does not exist, create id
        if queue_name not in self.queues_and_workers:
            self.log.debug(f"Initializing workers list for queue: {queue_name}")
            # Initialize the worker pids list for the queue
            self.queues_and_workers[queue_name] = []

        child_pid = self.__create_child_process(queue_name=queue_name, status_checker=status_checker)
        # If creation of the child process was successful
        if child_pid:
            self.log.debug(f"Assigning a new worker process with pid: {child_pid}, to queue: {queue_name}")
            # append the pid to the workers list of the queue_name
            (self.queues_and_workers[queue_name]).append(child_pid)

    # Forks a child process
    def __create_child_process(self, queue_name, status_checker=False) -> int:
        self.log.debug(f"Trying to create a new worker process for queue: {queue_name}")
        try:
            # TODO: Try to utilize Popen() instead of fork()
            created_pid = fork()
        except Exception as os_error:
            self.log.error(f"Failed to create a child process, reason: {os_error}")
            return 0

        if created_pid != 0:
            return created_pid

        try:
            # Clean unnecessary data
            # self.queues_and_workers = None
            if status_checker:
                child_worker = JobStatusWorker(
                    db_url=self.db_url,
                    rabbitmq_url=self.rabbitmq_url,
                    queue_name=queue_name,
                    test_sbatch=self.test_sbatch
                )
            else:
                child_worker = Worker(
                    db_url=self.db_url,
                    rabbitmq_url=self.rabbitmq_url,
                    queue_name=queue_name,
                    test_sbatch=self.test_sbatch
                )
            child_worker.run()
            exit(0)
        except Exception as e:
            self.log.error(f"Worker process failed for queue: {queue_name}, reason: {e}")
            exit(-1)

    def kill_workers(self):
        interrupted_pids = []
        self.log.info(f"Starting to send SIGINT to all workers")
        # Send SIGINT to all workers
        for queue_name in self.queues_and_workers:
            self.log.debug(f"Sending SIGINT to workers of queue: {queue_name}")
            for worker_pid in self.queues_and_workers[queue_name]:
                self.log.debug(f"Sending SIGINT to worker pid: {worker_pid}")
                try:
                    process = psutil.Process(pid=worker_pid)
                    process.send_signal(signal.SIGINT)
                    interrupted_pids.append(worker_pid)
                except psutil.ZombieProcess as error:
                    self.log.debug(f"Worker process has become a zombie: {worker_pid}, {error}")
                except psutil.NoSuchProcess as error:
                    self.log.error(f"No such worker process with pid: {worker_pid}, {error}")
                    continue
                except psutil.AccessDenied as error:
                    self.log.error(f"Access denied to the worker process with pid: {worker_pid}, {error}")
                    continue
        sleep(3)
        self.log.info(f"Starting to send SIGKILL to all workers if needed")
        # Check whether workers exited properly
        for pid in interrupted_pids:
            try:
                process = psutil.Process(pid=pid)
                self.log.debug(f"Sending SIGKILL to worker pid: {pid}")
                process.send_signal(signal.SIGKILL)
            except psutil.ZombieProcess:
                self.log.debug(f"Worker process became zombie: {pid}")
            except psutil.NoSuchProcess:
                self.log.debug(f"Worker process is not existing: {pid}")
