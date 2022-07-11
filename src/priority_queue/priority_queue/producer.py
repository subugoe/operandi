import time

from .constants import (
    DEFAULT_QUEUE_SERVER_TO_BROKER as DEFAULT_QSB,
    DEFAULT_QUEUE_BROKER_TO_SERVER as DEFAULT_QBS,
)

from .message_exchanger import MessageExchanger


class Producer:
    """
    Producer class used by the OPERANDI Server
    """

    def __init__(self, username, password):
        self.__messageExchanger = MessageExchanger(username, password)

        # It is enough to declare them once, however, to avoid
        # any dependencies (which module to start first), we
        # declare these both inside the producer and the consumer

        # Declare the queue to which the Producer pushes data
        self.__messageExchanger.declare_queue(DEFAULT_QSB)
        # Bind the queue to the Exchanger agent
        self.__messageExchanger.bind_queue(DEFAULT_QSB)

        # Declare the queue from which the Producer receives
        # responses from the Service broker
        self.__messageExchanger.declare_queue(DEFAULT_QBS)
        # Bind the queue to the Exchanger agent
        self.__messageExchanger.bind_queue(DEFAULT_QBS)

    def publish_mets_url(self, body):
        self.__messageExchanger.basic_publish(routing_key=DEFAULT_QSB,
                                              body=body)

    # TODO: Clarify that better
    # The producer (operandi-server) is also a consumer
    # for replies back from the consumer (service-broker)

    # Listens for messages coming from the QBS
    def define_consuming_listener(self, callback):
        # Define a basic consume method and its callback function
        # The 'callback' is the function to be called
        # when consuming from the respective queue
        self.__messageExchanger.channel.basic_consume(
            queue=DEFAULT_QBS,
            on_message_callback=callback,
            auto_ack=True
        )

        self.__messageExchanger.channel.start_consuming()

    # For getting back the cluster Job ID
    # TODO: This should be implemented properly with a Thread
    # TODO: Thread
    def receive_job_id(self):
        # Temporal solution, bad to do that in that way!
        while True:
            method_frame, header_frame, body = self.__messageExchanger.channel.basic_get(DEFAULT_QBS)
            if method_frame:
                # print(f"{method_frame}, {header_frame}, {body}")
                self.__messageExchanger.channel.basic_ack(method_frame.delivery_tag)
                if body:
                    job_id = body.decode('utf8')
                    return job_id

            # Check for new messages every 1 second
            time.sleep(1)
