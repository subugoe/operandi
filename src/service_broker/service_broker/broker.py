import logging
from os import fork, getpid, kill
from signal import SIGINT

from .constants import LOG_FORMAT, LOG_LEVEL
from .worker import Worker


class ServiceBroker:
    def __init__(self, rmq_host, rmq_port, rmq_vhost, hpc_host, hpc_username, hpc_key_path):
        broker_logger_name = f"{__name__}[{getpid()}]"
        self.log = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
        logging.getLogger('pika').setLevel(logging.WARNING)
        logging.getLogger(broker_logger_name).setLevel(LOG_LEVEL)

        self.rmq_host = rmq_host
        self.rmq_port = rmq_port
        self.rmq_vhost = rmq_vhost

        self.hpc_host = hpc_host
        self.hpc_username = hpc_username
        self.hpc_key_path = hpc_key_path

        # A dictionary to keep track of queues and worker pids
        # Keys: Each key is a unique queue name
        # Value: List of worker pids consuming from the key queue name
        self.queues_and_workers = {}

    # Creates a separate worker process and append its pid if successful
    def create_worker_process(self, queue_name) -> None:
        # If the entry for queue_name does not exist, create id
        if queue_name not in self.queues_and_workers:
            self.log.debug(f"Initializing workers list for queue: {queue_name}")
            # Initialize the worker pids list for the queue
            self.queues_and_workers[queue_name] = []

        child_pid = self.__create_child_process(queue_name)
        # If creation of the child process was successful
        if child_pid:
            self.log.debug(f"Assigning a new worker process with pid: {child_pid}, to queue: {queue_name}")
            # append the pid to the workers list of the queue_name
            (self.queues_and_workers[queue_name]).append(child_pid)

    # Forks a child process
    def __create_child_process(self, queue_name) -> int:
        self.log.debug(f"Trying to create a new worker process for queue: {queue_name}")
        try:
            created_pid = fork()
        except Exception as os_error:
            self.log.error(f"Failed to create a child process, reason: {os_error}")
            return 0
        if created_pid == 0:
            try:
                # Clean unnecessary data
                # self.queues_and_workers = None
                child_worker = Worker(self.rmq_host, self.rmq_port, self.rmq_vhost, queue_name)
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
