from logging import Logger
from os import fork
import psutil
import signal
from time import sleep
from typing import Dict

from .job_worker_download import JobWorkerDownload
from .job_worker_status import JobWorkerStatus
from .job_worker_submit import JobWorkerSubmit


# Forks a child process
def create_child_process(
    logger: Logger, db_url: str, rabbitmq_url: str, queue_name: str, worker_type: str, test_batch: bool
) -> int:
    logger.info(f"Trying to create a new worker process for queue: {queue_name}")
    try:
        created_pid = fork()
    except Exception as os_error:
        logger.error(f"Failed to create a child process, reason: {os_error}")
        return 0

    if created_pid != 0:
        return created_pid
    try:
        if worker_type == "status_worker":
            child_worker = JobWorkerStatus(db_url, rabbitmq_url, queue_name)
            child_worker.run(hpc_executor=True, hpc_io_transfer=False, publisher=True)
        elif worker_type == "download_worker":
            child_worker = JobWorkerDownload(db_url, rabbitmq_url, queue_name)
            child_worker.run(hpc_executor=True, hpc_io_transfer=True, publisher=False)
        else:  # worker_type == "submit_worker"
            child_worker = JobWorkerSubmit(db_url, rabbitmq_url, queue_name, test_batch)
            child_worker.run(hpc_executor=True, hpc_io_transfer=True, publisher=False)
        exit(0)
    except Exception as e:
        logger.error(f"Worker process failed for queue: {queue_name}, reason: {e}")
        exit(-1)


def send_signal_to_worker(logger: Logger, worker_pid: int, signal_type: signal):
    try:
        process = psutil.Process(pid=worker_pid)
        process.send_signal(signal_type)
    except psutil.ZombieProcess as error:
        logger.info(f"Worker process has become a zombie: {worker_pid}, {error}")
    except psutil.NoSuchProcess as error:
        logger.error(f"No such worker process with pid: {worker_pid}, {error}")
    except psutil.AccessDenied as error:
        logger.error(f"Access denied to the worker process with pid: {worker_pid}, {error}")


def kill_workers(logger: Logger, queues_and_workers: Dict):
    interrupted_pids = []
    logger.info(f"Starting to send SIGINT to all workers")
    # Send SIGINT to all workers
    for queue_name in queues_and_workers:
        logger.info(f"Sending SIGINT to workers of queue: {queue_name}")
        for worker_pid in queues_and_workers[queue_name]:
            send_signal_to_worker(logger, worker_pid=worker_pid, signal_type=signal.SIGINT)
            interrupted_pids.append(worker_pid)
    sleep(3)
    logger.info(f"Sending SIGKILL (if needed) to previously interrupted workers")
    # Check whether workers exited properly
    for pid in interrupted_pids:
        send_signal_to_worker(logger, worker_pid=pid, signal_type=signal.SIGKILL)
