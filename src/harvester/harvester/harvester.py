import os
import datetime
import time
import requests

import logging

from ocrd_webapi.rabbitmq import RMQPublisher
from rabbit_mq_utils.constants import (
    RABBIT_MQ_HOST as RMQ_HOST,
    RABBIT_MQ_PORT as RMQ_PORT,
    DEFAULT_EXCHANGER_NAME,
    DEFAULT_EXCHANGER_TYPE,
    DEFAULT_QUEUE_HARVESTER_TO_BROKER
)
from .constants import (
    VD18_IDS_FILE,
    VD18_URL,
    VD18_METS_EXT,
    WAIT_TIME_BETWEEN_SUBMITS,
    LOG_LEVEL,
    LOG_FORMAT,
)


# TODO: The harvester module will change completely
# Currently, the harvester communicates with the Service broker
# over the Operandi Server. This should change. The harvester
# will talk directly to the broker over the RabbitMQ.
# The current Harvester section in the README file will also be removed.
class Harvester:
    def __init__(self, rabbit_mq_host=RMQ_HOST, rabbit_mq_port=RMQ_PORT):

        logger = logging.getLogger(__name__)
        # Set the global logging level to INFO
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
        # Set the Harvester logging level to LOG_LEVEL
        logging.getLogger(__name__).setLevel(LOG_LEVEL)
        self._logger = logger

        self.vd18_file = VD18_IDS_FILE
        self.wtbs = WAIT_TIME_BETWEEN_SUBMITS
        if not os.path.exists(self.vd18_file) or not os.path.isfile(self.vd18_file):
            self._logger.error(f"{self.vd18_file} file does not exist or is not a readable file!")
            exit(1)

        self.__publisher = self.__initiate_publisher(
            rabbit_mq_host,
            rabbit_mq_port,
            logger_name="operandi-harvester_publisher_harvester-queue"
        )
        self.__publisher.create_queue(
            queue_name=DEFAULT_QUEUE_HARVESTER_TO_BROKER,
            exchange_name=DEFAULT_EXCHANGER_NAME,
            exchange_type=DEFAULT_EXCHANGER_TYPE
        )

    @staticmethod
    def url_exists(url):
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                # print(f"Headers: {response.headers}")
                # print(f"Content size: {response.content.__sizeof__() - 33}")
                return True

        except requests.exceptions.RequestException as e:
            # print(f"f:url_exists, Exception: {e}")
            return False

    # 1. Checks if the mets_id exits
    # 2. Sends the mets_url, mets_id to the harvester-to-broker queue
    def __harvest_one_mets(self, mets_id):
        # print(f"INFO: Harvesting... {mets_id}")
        if not mets_id:
            return False

        mets_url = f"{VD18_URL}{mets_id}{VD18_METS_EXT}"
        if Harvester.url_exists(mets_url):
            # Create a timestamp
            timestamp = datetime.datetime.now().strftime("_%Y%m%d_%H%M")
            # Append the timestamp at the end of the provided workspace_id
            mets_id += timestamp
            publish_message = f"{mets_url},{mets_id}".encode('utf8')

            try:
                self.__publisher.publish_to_queue(
                    exchange_name=DEFAULT_EXCHANGER_NAME,
                    queue_name=DEFAULT_QUEUE_HARVESTER_TO_BROKER,
                    message=publish_message,
                )
                self._logger.info(f"Mets `{mets_id}` was sent successfully.")
                return True
            except Exception as e:
                self._logger.error(f"Mets `{mets_id}` was no sent successfully. Reason: {e}")
        return False

    def __print_waiting_message(self):
        print(f"INFO: Waiting for few seconds... ", end=" ")
        for i in range(self.wtbs, 0, -1):
            print(f"{i}", end=" ")
            if i == 1:
                print()
            time.sleep(1)

    # TODO: implement proper start and stop mechanisms
    def start_harvesting(self, limit=0):
        self._logger.info(f"Harvesting started with limit:{limit}")
        self._logger.info(f"Mets URL will be submitted every {self.wtbs} seconds.")
        harvested_counter = 0

        # Reads vd18 file line by line
        with open(self.vd18_file, mode="r") as f:
            for line in f:
                if not line:
                    break
                mets_id = line.strip()
                self.__harvest_one_mets(mets_id)
                harvested_counter += 1
                # If the limit is reached stop harvesting
                if harvested_counter == limit:
                    break
                self.__print_waiting_message()

    # TODO: implement proper start and stop mechanisms
    def stop_harvesting(self):
        self._logger.info("Stopped harvesting")

    @staticmethod
    def __initiate_publisher(rabbit_mq_host, rabbit_mq_port, logger_name):
        publisher = RMQPublisher(
            host=rabbit_mq_host,
            port=rabbit_mq_port,
            vhost="/",
            logger_name=logger_name
        )
        publisher.authenticate_and_connect(
            username="operandi-harvester",
            password="operandi-harvester"
        )
        publisher.enable_delivery_confirmations()
        return publisher
