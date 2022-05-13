import pika

from .constants import (
    RABBIT_MQ_IP as IP,
    RABBIT_MQ_PORT as PORT,
    DEFAULT_EXCHANGER_NAME as EXCHANGER,
    DEFAULT_EXCHANGER_TYPE as EX_TYPE,
    DEFAULT_QUEUE_NAME as Q_NAME,
)


class Consumer:
    """
    Consumer class used by the Service-broker
    """

    def __init__(self, host=IP, port=PORT, exchanger=EXCHANGER,
                 exchanger_type=EX_TYPE, queue=Q_NAME):
        # Establish a connection with the RabbitMQ server.
        self.__create_connection(host, port)
        self.__create_channel(exchanger, exchanger_type)

        # Create a queue
        self.__create_queue(queue)

        # Bind the queue to the exchange agent, without a routing/binding key
        # May be not needed without a routing/binding key
        self.__channel.queue_bind(exchange=EXCHANGER,
                                  queue=Q_NAME)

    def __del__(self):
        if self.__connection.is_open:
            self.__connection.close()

    def __create_connection(self, host, port):
        self.__parameters = pika.ConnectionParameters(host=host, port=port)
        self.__connection = pika.BlockingConnection(self.__parameters)

    def __create_channel(self, exchange, exchange_type):
        if self.__connection.is_open:
            self.__channel = self.__connection.channel()
            self.__channel.exchange_declare(exchange=exchange,
                                            exchange_type=exchange_type)

    def __create_queue(self, queue, durability=False):
        if self.__connection.is_open and self.__channel.is_open:
            self.__channel.queue_declare(queue=queue, durable=durability)

    # Configure the basic consume method for a queue
    # Continuously consumes workspaces from the "queue"
    def __basic_consume(self, queue, callback, auto_ack=False):
        # 'callback' is the function to be called
        # when consuming from the queue
        self.__channel.basic_consume(queue=queue,
                                     on_message_callback=callback,
                                     auto_ack=auto_ack)

    # Consumes a single message from the channel
    def __single_consume(self, queue):
        method_frame, header_frame, body = self.__channel.basic_get(queue)
        if method_frame:
            # print(f"{method_frame}, {header_frame}, {body}")
            self.__channel.basic_ack(method_frame.delivery_tag)
            return body
        else:
            # print(f"No message returned")
            return None

    def set_callback(self, callback):
        self.__basic_consume(queue=Q_NAME, callback=callback, auto_ack=True)

    # Wrapper for __single_consume
    def single_consume(self):
        return self.__single_consume(Q_NAME)

    # TODO: implement proper start/stop methods
    def start_consuming(self):
        print(f"INFO: Waiting for messages. To exit press CTRL+C.")
        self.__channel.start_consuming()

    def stop_consuming(self):
        print(f"INFO: The consumer has stopped consuming.")
        self.__channel.stop_consuming()


# 'default_callback' is the default function
# to be called when consuming from the queue
def default_callback(ch, method, properties, body):
    # print(f"INFO_Default: ch: {ch}")
    # print(f"INFO_Default: method: {method}")
    # print(f"INFO_Default: properties: {properties}")
    print(f"INFO_Default: A message has been received: {body}")


def main():
    consumer = Consumer()

    # Start listening for messages
    consumer.set_callback(callback=default_callback)
    consumer.start_consuming()


if __name__ == "__main__":
    main()
