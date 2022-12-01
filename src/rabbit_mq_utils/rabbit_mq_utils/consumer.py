from .constants import (
    DEFAULT_QUEUE_SERVER_TO_BROKER as DEFAULT_QSB
)
from .message_exchanger import MessageExchanger


class Consumer:
    """
    Consumer class used by the Service-broker
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

    # Listens for messages coming from the QSB
    def define_queue_listener(self, callback):
        # The 'callback' is the function to be called
        # when a message is received from the queue
        self.__messageExchanger.receive_from_queue(
            queue_name=DEFAULT_QSB,
            callback=callback,
            auto_ack=False  # acks must be sent manually
        )

        self.__messageExchanger.channel.start_consuming()
