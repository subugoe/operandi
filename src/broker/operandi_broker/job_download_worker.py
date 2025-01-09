from logging import getLogger
import signal
from os import getpid, getppid, setsid
from sys import exit

from operandi_utils import reconfigure_all_loggers, get_log_file_path_prefix
from operandi_utils.constants import LOG_LEVEL_WORKER
from operandi_utils.database import sync_db_initiate_database
from operandi_utils.hpc import NHRExecutor, NHRTransfer
from operandi_utils.rabbitmq import get_connection_consumer


class JobDownloadWorker:
    def __init__(self, db_url, rabbitmq_url, queue_name, tunnel_port_executor, tunnel_port_transfer, test_sbatch=False):
        self.log = getLogger(f"operandi_broker.job_download_worker[{getpid()}].{queue_name}")
        self.queue_name = queue_name
        self.log_file_path = f"{get_log_file_path_prefix(module_type='worker')}_{queue_name}.log"
        self.test_sbatch = test_sbatch

        self.db_url = db_url
        self.rmq_url = rabbitmq_url
        self.rmq_consumer = None
        self.hpc_executor = None
        self.hpc_io_transfer = None

        # Currently consumed message related parameters
        self.current_message_delivery_tag = None
        self.current_message_job_id = None
        self.has_consumed_message = False

        self.tunnel_port_executor = tunnel_port_executor
        self.tunnel_port_transfer = tunnel_port_transfer

    def __del__(self):
        if self.rmq_consumer:
            self.rmq_consumer.disconnect()

    def run(self):
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
            self.hpc_executor = NHRExecutor()
            self.log.info("HPC executor connection successful.")
            self.hpc_io_transfer = NHRTransfer()
            self.log.info("HPC transfer connection successful.")

            self.rmq_consumer = get_connection_consumer(rabbitmq_url=self.rmq_url)
            self.log.info(f"RMQConsumer connected")
            self.rmq_consumer.configure_consuming(queue_name=self.queue_name, callback_method=self.__callback)
            self.log.info(f"Configured consuming from queue: {self.queue_name}")
            self.log.info(f"Starting consuming from queue: {self.queue_name}")
            self.rmq_consumer.start_consuming()
        except Exception as e:
            self.log.error(f"The worker failed, reason: {e}")
            raise Exception(f"The worker failed, reason: {e}")

    def __callback(self, ch, method, properties, body):
        pass

    def __handle_message_failure(self, interruption: bool = False):
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

    # TODO: Ideally this method should be wrapped to be able
    #  to pass internal data from the Worker class required for the cleaning
    # The arguments to this method are passed by the caller from the OS
    def signal_handler(self, sig, frame):
        signal_name = signal.Signals(sig).name
        self.log.info(f"{signal_name} received from parent process `{getppid()}`.")
        if self.has_consumed_message:
            self.log.info(f"Handling the message failure due to interruption: {signal_name}")
            self.__handle_message_failure(interruption=True)
        self.rmq_consumer.disconnect()
        self.rmq_consumer = None
        self.log.info("Exiting gracefully.")
        exit(0)
