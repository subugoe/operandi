import pika

from .constants import (
    RABBIT_MQ_IP as IP,
    RABBIT_MQ_PORT as PORT,
    DEFAULT_EXCHANGER_NAME as EXCHANGER,
    DEFAULT_EXCHANGER_TYPE as EX_TYPE,
    DEFAULT_QUEUE_NAME as Q_NAME,
)


class Producer:
    """
    Producer class used by the OPERANDI Server
    """

    def __init__(self, host=IP, port=PORT, exchanger=EXCHANGER,
                 exchanger_type=EX_TYPE, queue=Q_NAME):
        # Establish a connection with the RabbitMQ server.
        self.__create_connection(host, port)
        self.__create_channel(exchanger, exchanger_type)

        # Create a queue
        self.__create_queue(queue)

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
                                     routing_key=Q_NAME,
                                     body=body,
                                     properties=message_properties,
                                     mandatory=True)


def main():
    producer = Producer()
    message = "Hello World!"

    producer.basic_publish(message)
    print(f"The producer has sent: {message}")

    # Flush network buffers by deleting the object reference
    # so the destructor is triggered and the connection is closed
    del producer


if __name__ == "__main__":
    main()
