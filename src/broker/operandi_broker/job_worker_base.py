from logging import getLogger
import signal
from os import getpid, getppid, setsid
from sys import exit

from operandi_utils import reconfigure_all_loggers, get_log_file_path_prefix
from operandi_utils.constants import LOG_LEVEL_WORKER
from operandi_utils.database import sync_db_initiate_database
from operandi_utils.hpc import NHRExecutor, NHRTransfer
from operandi_utils.rabbitmq import get_connection_consumer, get_connection_publisher

NOT_IMPLEMENTED_ERROR: str = "The method was not implemented in the extending class"

# Each worker class listens to a specific queue, consumes messages, and processes messages.
class JobWorkerBase:
    def __init__(self, db_url, rabbitmq_url, queue_name):
        self.db_url = db_url
        self.rmq_url = rabbitmq_url
        self.queue_name = queue_name

        self.log = getLogger(f"operandi_broker.worker.{self.queue_name}_{getpid()}")
        self.log_file_path = f"{get_log_file_path_prefix(module_type='worker')}_{self.queue_name}_{getpid()}.log"

        self.rmq_consumer = None
        self.rmq_publisher = None
        self.hpc_executor = None
        self.hpc_io_transfer = None

        self.has_consumed_message = False
        self.current_message_delivery_tag = None

    def disconnect_rmq_connections(self):
        self.log.info("Disconnecting existing RabbitMQ connections.")
        if self.rmq_consumer:
            self.log.info("Disconnecting the RMQ consumer")
            self.rmq_consumer.disconnect()
        if self.rmq_publisher:
            self.log.info("Disconnecting the RMQ publisher")
            self.rmq_publisher.disconnect()

    def __del__(self):
        self.disconnect_rmq_connections()

    def _consumed_msg_callback(self, ch, method, properties, body):
        raise NotImplementedError(NOT_IMPLEMENTED_ERROR)

    def _handle_msg_failure(self, interruption: bool):
        raise NotImplementedError(NOT_IMPLEMENTED_ERROR)

    def run(self, hpc_executor: bool, hpc_io_transfer: bool, publisher: bool):
        try:
            # Source: https://unix.stackexchange.com/questions/18166/what-are-session-leaders-in-ps
            # Make the current process session leader
            setsid()
            # Reconfigure all loggers to the same format
            reconfigure_all_loggers(log_level=LOG_LEVEL_WORKER, log_file_path=self.log_file_path)
            self.log.info(f"Activating signal handler for SIGINT, SIGTERM")
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            sync_db_initiate_database(self.db_url)
            self.log.info("MongoDB connection successful.")
            if hpc_executor:
                self.hpc_executor = NHRExecutor()
                self.log.info("HPC executor connection successful.")
            if hpc_io_transfer:
                self.hpc_io_transfer = NHRTransfer()
                self.log.info("HPC transfer connection successful.")
            if publisher:
                self.rmq_publisher = get_connection_publisher(rabbitmq_url=self.rmq_url, enable_acks=True)
                self.log.info(f"RMQPublisher connected")

            self.rmq_consumer = get_connection_consumer(rabbitmq_url=self.rmq_url)
            self.log.info(f"RMQConsumer connected")
            self.rmq_consumer.configure_consuming(
                queue_name=self.queue_name, callback_method=self._consumed_msg_callback)
            self.log.info(f"Starting consuming from queue: {self.queue_name}")
            self.rmq_consumer.start_consuming()
        except Exception as e:
            self.log.error(f"The worker failed, reason: {e}")
            raise Exception(f"The worker failed, reason: {e}")

    # The arguments to this method are passed by the caller from the OS
    def signal_handler(self, sig, frame):
        signal_name = signal.Signals(sig).name
        self.log.info(f"{signal_name} received from parent process `{getppid()}`.")
        if self.has_consumed_message:
            self.log.info(f"Handling the consumed message failure due to an interruption: {signal_name}")
            self._handle_msg_failure(interruption=True)
        # TODO: Verify if this call here is necessary
        self.disconnect_rmq_connections()
        self.log.info("Exiting gracefully.")
        exit(0)
