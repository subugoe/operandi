import logging
from os import fork, kill
from signal import SIGINT

from operandi_utils import (
    verify_database_uri,
    verify_and_parse_mq_uri
)
from .worker import Worker
from .job_status_worker import JobStatusWorker


class ServiceBroker:
    def __init__(self, db_url: str, rabbitmq_url: str, test_sbatch: bool = False):
        self.log = logging.getLogger(__name__)
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
        if created_pid == 0:
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
        return created_pid

    def kill_workers(self):
        for queue_name in self.queues_and_workers:
            self.log.debug(f"Sending SIGINT to workers of queue: {queue_name}")
            for worker_pid in self.queues_and_workers[queue_name]:
                self.log.debug(f"Sending SIGINT to worker_pid: {worker_pid}")
                kill(worker_pid, SIGINT)
