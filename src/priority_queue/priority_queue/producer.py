import pika

from .constants import (
    RABBIT_MQ_HOST as HOST,
    RABBIT_MQ_PORT as PORT,
    DEFAULT_EXCHANGER_NAME as EXCHANGER,
    DEFAULT_EXCHANGER_TYPE as EX_TYPE,
    DEFAULT_QUEUE_SERVER_TO_BROKER as QUEUE_S_TO_B,
    DEFAULT_QUEUE_BROKER_TO_SERVER as QUEUE_B_TO_S,
)


class Producer:
    """
    Producer class used by the OPERANDI Server
    """

    def __init__(self, host=HOST, port=PORT, exchanger=EXCHANGER,
                 exchanger_type=EX_TYPE):
        # Establish a connection with the RabbitMQ server.
        self.__create_connection(host, port)
        self.__create_channel(exchanger, exchanger_type)

        # Create the queues (same for both Producer and Consumer)
        self.__create_queue(QUEUE_S_TO_B)
        self.__create_queue(QUEUE_B_TO_S)

    def __del__(self):
        if self.__connection.is_open:
            self.__connection.close()

    def __create_connection(self, host, port):
        self.__parameters = pika.ConnectionParameters(host=host, port=port)
        self.__connection = pika.BlockingConnection(self.__parameters)

    def __create_channel(self, exchange, exchange_type):
        if self.__connection.is_open:
            self.__channel = self.__connection.channel()
            if self.__channel.is_open:
                self.__channel.exchange_declare(exchange=exchange,
                                                exchange_type=exchange_type)

    def __create_queue(self, queue, durability=False):
        if self.__connection.is_open and self.__channel.is_open:
            self.__channel.queue_declare(queue=queue, durable=durability)

    def basic_publish(self, body, durable=False):
        if durable:
            delivery_mode = pika.spec.PERSISTENT_DELIVERY_MODE
        else:
            delivery_mode = pika.spec.TRANSIENT_DELIVERY_MODE

        message_properties = pika.BasicProperties(
            delivery_mode=delivery_mode
        )

        # Publish the message body through the exchanger agent
        self.__channel.basic_publish(exchange=EXCHANGER,
                                     routing_key=QUEUE_S_TO_B,
                                     body=body,
                                     properties=message_properties,
                                     mandatory=True)

    # For getting back the cluster Job ID
    # TODO: This should be implemented properly with a new class named MessageExchanger
    def read_job_id(self):
        method_frame, header_frame, body = self.__channel.basic_get(QUEUE_B_TO_S)
        if method_frame:
            # print(f"{method_frame}, {header_frame}, {body}")
            self.__channel.basic_ack(method_frame.delivery_tag)
            return body
        else:
            # print(f"No message returned")
            return None
