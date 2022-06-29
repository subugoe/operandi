import pika

from .constants import (
    RABBIT_MQ_HOST as HOST,
    RABBIT_MQ_PORT as PORT,
    DEFAULT_EXCHANGER_NAME as EXCHANGER,
    DEFAULT_EXCHANGER_TYPE as EX_TYPE,
)


class MessageExchanger:
    """
    MessageExchanger class used by the
    Producer and Consumer classes
    """

    def __init__(self, host=HOST, port=PORT):

        self.__rabbitMQ_host = host
        self.__rabbitMQ_port = port

        # Establish a TCP connection with the RabbitMQ server.
        self.__connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host, port=port)
        )

        # Create a channel (session) to be used by the current instance
        self.channel = None
        self.__create_channel()

    # Create a channel and bind an exchanger agent to it
    # The exchanger agent is responsible to transfer
    # messages based on the exchange type
    def __create_channel(self, exchange=EXCHANGER, exchange_type=EX_TYPE):
        if self.__connection.is_open:
            self.channel = self.__connection.channel()
            self.channel.exchange_declare(exchange=exchange,
                                          exchange_type=exchange_type)

    # The Operandi server declares the QUEUE_S_TO_B to publish to the Broker
    # The Service broker declares the QUEUE_B_TO_S to response back to the Server
    def declare_queue(self, queue_name, durability=False):
        if self.__connection.is_open and self.channel.is_open:
            self.channel.queue_declare(queue=queue_name, durable=durability)

    # The Operandi server binds the QUEUE_S_TO_B to the Exchanger agent
    # The Service broker binds the QUEUE_B_TO_S to the Exchanger agent
    def bind_queue(self, queue, exchange=EXCHANGER):
        if self.__connection.is_open and self.channel.is_open:
            self.channel.queue_bind(queue=queue, exchange=exchange)

    # The Operandi server publishes to routing_key=QUEUE_S_TO_B
    # The Service broker publishes to routing_key=QUEUE_B_TO_S
    def basic_publish(self, routing_key, body, durable=False):
        if durable:
            delivery_mode = pika.spec.PERSISTENT_DELIVERY_MODE
        else:
            delivery_mode = pika.spec.TRANSIENT_DELIVERY_MODE

        message_properties = pika.BasicProperties(
            delivery_mode=delivery_mode
        )

        # Publish the message body through the exchanger agent
        self.channel.basic_publish(exchange=EXCHANGER,
                                   routing_key=routing_key,
                                   body=body,
                                   properties=message_properties,
                                   mandatory=True)

    # The Operandi server consumes from routing_key=QUEUE_B_TO_S
    # The Service broker consumes from routing_key=QUEUE_S_TO_B
    def basic_consume(self, queue_name, callback, auto_ack=False):
        # The 'callback' is the function to be called
        # when consuming from the respective queue
        # Both modules declare their own callback handlers separately
        self.channel.basic_consume(queue=queue_name,
                                   on_message_callback=callback,
                                   auto_ack=auto_ack)
