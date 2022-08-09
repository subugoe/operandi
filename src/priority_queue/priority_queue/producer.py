import time
from .message_exchanger import MessageExchanger
from .constants import (
    DEFAULT_QUEUE_SERVER_TO_BROKER as DEFAULT_QSB,
    DEFAULT_QUEUE_BROKER_TO_SERVER as DEFAULT_QBS
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

    # TODO: Clarify that better
    # The producer (operandi-server) is also a consumer
    # for replies back from the consumer (service-broker)

    # Listens for messages coming from the QBS
    def define_queue_listener(self, callback):
        # The 'callback' is the function to be called
        # when a message is received from the queue
        self.__messageExchanger.receive_from_queue(
            queue_name=DEFAULT_QBS,
            callback=callback,
            auto_ack=True
        )

        self.__messageExchanger.channel.start_consuming()

        """
        # The 'callback' is the function to be called
        # when consuming from the respective queue
        self.__messageExchanger.channel.basic_consume(
            queue=DEFAULT_QBS,
            on_message_callback=callback,
            auto_ack=True
        )

        self.__messageExchanger.channel.start_consuming()
        """

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
