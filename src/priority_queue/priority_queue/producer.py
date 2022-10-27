import time
from .message_exchanger import MessageExchanger
from .constants import (
    DEFAULT_QUEUE_SERVER_TO_BROKER as DEFAULT_QSB
)


class Producer:
    """
    Producer class used by the OPERANDI Server
    """
    def __init__(self, username, password, rabbit_mq_host, rabbit_mq_port):
        self.__messageExchanger = MessageExchanger(username,
                                                   password,
                                                   rabbit_mq_host,
                                                   rabbit_mq_port)

        # It is enough to configure them once, however, to avoid
        # any module dependencies, i.e. which module to start first,
        # defaults are configured both in the Producer and the Consumer
        self.__messageExchanger.configure_default_queues()

    def publish_mets_url(self, body):
        self.__messageExchanger.send_to_queue(queue_name=DEFAULT_QSB, message=body)
        # self.__messageExchanger.basic_publish(routing_key=DEFAULT_QSB, body=body)
