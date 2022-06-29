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

    def __init__(self):
        self.__messageExchanger = MessageExchanger()

        # Declaring and binding queues is done only once
        # This is already handled by the Producer class

    # Consumes a single message from the channel
    def single_consume_mets_url(self):
        while True:
            method_frame, header_frame, body = self.__messageExchanger.channel.basic_get(DEFAULT_QSB)
            if method_frame:
                # print(f"{method_frame}, {header_frame}, {body}")
                self.__messageExchanger.channel.basic_ack(method_frame.delivery_tag)
                if body:
                    mets_url, mets_id = body.decode('utf8').split(',')
                    return mets_url, mets_id

            time.sleep(1)

    # TODO: Replace this properly so a thread handles that
    # TODO: Thread
    def reply_job_id(self, cluster_job_id):
        # Publish the message body through the exchanger agent
        self.__messageExchanger.basic_publish(routing_key=DEFAULT_QBS,
                                              body=cluster_job_id)

    # TODO: implement proper start/stop methods
    def start_consuming(self):
        self.__messageExchanger.channel.start_consuming()
        print(f"INFO: Waiting for messages. To exit press CTRL+C.")

    def stop_consuming(self):
        self.__messageExchanger.channel.stop_consuming()
        print(f"INFO: The consumer has stopped consuming.")
