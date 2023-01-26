import asyncio
import json
import logging
import signal
from os import getpid, getppid, setsid
from sys import exit
from time import sleep

import ocrd_webapi.database as db
from ocrd_webapi.managers.nextflow_manager import NextflowManager
from ocrd_webapi.rabbitmq import RMQConsumer
from .constants import LOG_FORMAT, LOG_LEVEL


# Each worker class listens to a specific queue,
# consume messages, and process messages.
class Worker:
    def __init__(self, db_url, rmq_host, rmq_port, rmq_vhost, queue_name):
        worker_logger_name = f"{__name__}[{getpid()}]"
        self.log = logging.getLogger(worker_logger_name)
        # Set the global logging level to INFO
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
        logging.getLogger('pika').setLevel(logging.WARNING)
        # Set the ServiceBroker logging level to LOG_LEVEL
        logging.getLogger(worker_logger_name).setLevel(LOG_LEVEL)

        # Process ID of this worker
        self.pid = getpid()
        # Process ID of the service broker (parent)
        self.ppid = getppid()
        self.queue_name = queue_name

        self.db_url = db_url
        self.rmq_host = rmq_host
        self.rmq_port = rmq_port
        self.rmq_vhost = rmq_vhost
        self.rmq_username = "default-consumer"
        self.rmq_password = "default-consumer"
        self.rmq_consumer = None

    def run(self):
        try:
            # Source: https://unix.stackexchange.com/questions/18166/what-are-session-leaders-in-ps
            # Make the current process session leader
            setsid()
            self.log.debug(f"Activating signal handler for SIGINT")
            signal.signal(signal.SIGINT, sigint_signal_handler)
            loop = asyncio.get_event_loop()
            db_coroutine = db.initiate_database(self.db_url)
            loop.run_until_complete(db_coroutine)
            self.connect_consumer()
            self.configure_consuming(self.queue_name, self.__default_callback)
            self.start_consuming()
        except Exception as e:
            self.log.error(f"The worker failed to run, reason: {e}")
            raise Exception(f"The worker failed to run, reason: {e}")

    def connect_consumer(self):
        if self.rmq_consumer:
            # If for some reason connect_consumer() is called more than once.
            self.log.warning(f"The RMQConsumer was already instantiated. "
                             f"Overwriting the existing RMQConsumer.")
        self.log.debug(f"Connecting RMQConsumer to RabbitMQ server: "
                       f"{self.rmq_host}:{self.rmq_port}{self.rmq_vhost}")
        self.rmq_consumer = RMQConsumer(host=self.rmq_host, port=self.rmq_port, vhost=self.rmq_vhost)
        # TODO: Remove this information before the release
        self.log.debug(f"RMQConsumer authenticates with username: "
                       f"{self.rmq_username}, password: {self.rmq_password}")
        self.rmq_consumer.authenticate_and_connect(username=self.rmq_username, password=self.rmq_password)
        self.log.debug(f"Successfully connected RMQConsumer.")

    def configure_consuming(self, queue_name, callback_method):
        if not self.rmq_consumer:
            raise Exception("The RMQConsumer connection is not configured or broken")
        self.log.debug(f"Configuring the consuming for queue: {queue_name}")
        self.rmq_consumer.configure_consuming(
            queue_name=queue_name,
            callback_method=callback_method
        )

    def start_consuming(self):
        if not self.rmq_consumer:
            raise Exception("The RMQConsumer connection is not configured or broken")
        self.log.debug(f"Starting consuming from queue: {self.queue_name}")
        self.rmq_consumer.start_consuming()

    # The callback method provided to the Consumer listener
    # The arguments to this method are passed by the caller
    def __default_callback(self, ch, method, properties, body):
        # Print information of the consumed message
        # self.log.debug(f"ch: {ch}, method: {method}, properties: {properties}, body: {body}")
        # self.log.debug(f"Consumed message: {body}")

        workflow_message = json.loads(body)
        self.log.info(f"Workflow Message: {workflow_message}")
        workflow_id = workflow_message.get("workflow_id", None)
        workspace_id = workflow_message.get("workspace_id", None)
        job_id = workflow_message.get("job_id", None)
        mets_name = workflow_message.get("mets_name", None)
        input_file_group = workflow_message.get("input_file_group", None)

        if not (workflow_id and workspace_id and job_id and mets_name and input_file_group):
            self.log.warning("A workflow message parameter is None")
            loop = asyncio.get_event_loop()
            self.log.debug(f"Setting new job state[FAILED] of job_id: {job_id}")
            db_coroutine = db.set_workflow_job_state(job_id, job_state="FAILED")
            loop.run_until_complete(db_coroutine)
            # ch.basic_nack(delivery_tag=method.delivery_tag)
            return

        loop = asyncio.get_event_loop()
        self.log.debug(f"Setting new job state[RUNNING] of job_id: {job_id}")
        db_coroutine = db.set_workflow_job_state(job_id, job_state="RUNNING")
        loop.run_until_complete(db_coroutine)

        # Simulate processing action
        sleep(15)
        loop = asyncio.get_event_loop()
        self.log.debug(f"Setting new job state[FINISHED] to of job_id: {job_id}")
        db_coroutine = db.set_workflow_job_state(job_id, job_state="FINISHED")
        loop.run_until_complete(db_coroutine)

        # Acknowledge back that message has been processed successfully
        ch.basic_ack(delivery_tag=method.delivery_tag)


# TODO: Ideally this method should be wrapped to be able
#  to pass internal data from the Worker class required for the cleaning
# The arguments to this method are passed by the caller from the OS
def sigint_signal_handler(sig, frame):
    print(f"pid: {getpid()}, received SIGINT signal from the service broker")
    # Sleeping to wait for some time before exiting
    sleep(1)
    # TODO: Nack the message that is currently being processed.
    # TODO: Disconnect the RMQConsumer properly
    # TODO: Clean the remaining leftovers (if any)
    sleep(1)
    print(f"pid: {getpid()}, the worker is exiting gracefully")
    exit(0)
