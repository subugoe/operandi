import time

from .constants import (
    DEFAULT_QUEUE_SERVER_TO_BROKER as DEFAULT_QSB,
    DEFAULT_QUEUE_BROKER_TO_SERVER as DEFAULT_QBS,
)

from .message_exchanger import MessageExchanger


class Consumer:
    """
    Consumer class used by the Service-broker
    """

    def __init__(self, username, password):
        self.__messageExchanger = MessageExchanger(username, password)

        # It is enough to declare them once, however, to avoid
        # any dependencies (which module to start first), we
        # declare and bind queues both inside the producer and the consumer

        # Declare the queue to which the Producer pushes data
        self.__messageExchanger.declare_queue(DEFAULT_QSB)
        # Bind the queue to the Exchanger agent
        self.__messageExchanger.bind_queue(DEFAULT_QSB)

        # Declare the queue from which the Producer receives
        # responses from the Service broker
        self.__messageExchanger.declare_queue(DEFAULT_QBS)
        # Bind the queue to the Exchanger agent
        self.__messageExchanger.bind_queue(DEFAULT_QBS)

    # Listens for messages coming from the QSB
    def define_consuming_listener(self, callback):
        # Define a basic consume method and its callback function
        # The 'callback' is the function to be called
        # when consuming from the respective queue
        self.__messageExchanger.channel.basic_consume(
            queue=DEFAULT_QSB,
            on_message_callback=callback,
            auto_ack=True
        )

        self.__messageExchanger.channel.start_consuming()

    # TODO: Clarify that better
    # The consumer (service-broker) is also a producer
    # for replies back to the producer (operandi-server)

    # TODO: Replace this properly so a thread handles that
    # TODO: Thread
    def reply_job_id(self, cluster_job_id):
        # Publish the message body through the exchanger agent
        self.__messageExchanger.basic_publish(routing_key=DEFAULT_QBS,
                                              body=cluster_job_id)
