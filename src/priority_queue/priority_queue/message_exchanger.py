import pika

from .constants import (
    RABBIT_MQ_HOST as HOST,
    RABBIT_MQ_PORT as PORT,
    RABBIT_MQ_DOCKER_HOST as DOCKER_HOST,
    DEFAULT_EXCHANGER_NAME as EXCHANGER,
    DEFAULT_EXCHANGER_TYPE as EX_TYPE,
)


class MessageExchanger:
    """
    MessageExchanger class used by the
    Producer and Consumer classes
    """

    # TODO: FIX THIS
    # Currently, the host has to be changed manually between HOST/DOCKER_HOST

    # Local credentials - guest, guest
    # Docker credentials - admin, admin
    def __init__(self, username, password, host=HOST, port=PORT):

        self.__rabbitMQ_host = host
        self.__rabbitMQ_port = port

        # Set the connection parameters
        conn_params = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=pika.PlainCredentials(
                username,
                password
            ),
            # TODO: The heartbeat should not be disabled (0)!
            # This is a temporal solution before using threads to handle tasks
            # Notes to myself:
            # Check here: https://stackoverflow.com/questions/51752890/how-to-disable-heartbeats-with-pika-and-rabbitmq
            # Check here: https://github.com/pika/pika/blob/0.12.0/examples/basic_consumer_threaded.py
            heartbeat=0
        )

        # Establish a TCP connection with the RabbitMQ server.
        self.__connection = pika.BlockingConnection(
            conn_params
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
        else:
            print("ERROR_create_channel: Connection is closed!")

    # The Operandi server declares the QUEUE_S_TO_B to publish to the Broker
    # The Service broker declares the QUEUE_B_TO_S to response back to the Server
    def declare_queue(self, queue_name, durability=False):
        if self.__connection.is_open and self.channel.is_open:
            self.channel.queue_declare(queue=queue_name, durable=durability)
        else:
            print("ERROR_declare_queue: Connection is closed!")

    # The Operandi server binds the QUEUE_S_TO_B to the Exchanger agent
    # The Service broker binds the QUEUE_B_TO_S to the Exchanger agent
    def bind_queue(self, queue, exchange=EXCHANGER):
        if self.__connection.is_open and self.channel.is_open:
            self.channel.queue_bind(queue=queue, exchange=exchange)
        else:
            print("ERROR_bind_queue: Connection is closed!")

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
