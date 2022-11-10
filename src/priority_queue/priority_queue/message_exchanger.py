import pika
from .constants import (
    RABBIT_MQ_HOST as HOST,
    RABBIT_MQ_PORT as PORT,
    DEFAULT_EXCHANGER_NAME as EXCHANGER,
    DEFAULT_EXCHANGER_TYPE as EXCHANGE_TYPE,
    DEFAULT_QUEUE_SERVER_TO_BROKER as DEFAULT_QSB,
)


class MessageExchanger:
    """
    MessageExchanger class used by the
    Producer and Consumer classes
    """
    def __init__(self, username, password, rabbit_mq_host=HOST, rabbit_mq_port=PORT):
        # Connection parameters
        self.__rabbit_mq_host = rabbit_mq_host
        self.__rabbit_mq_port = rabbit_mq_port
        self.__rabbit_mq_username = username
        self.__rabbit_mq_password = password

        # Set the connection parameters
        conn_params = self.__set_connection_parameters()

        # Establish a TCP connection with the RabbitMQ server.
        self.__connection = pika.BlockingConnection(conn_params)

        # Create a default channel (session) to be used by the current instance
        self.channel = None
        self.create_channel(EXCHANGER, EXCHANGE_TYPE)

    def __set_connection_parameters(self):
        connection_parameters = pika.ConnectionParameters(
            host=self.__rabbit_mq_host,
            port=self.__rabbit_mq_port,
            credentials=pika.PlainCredentials(
                # Local default credentials - guest, guest
                # Docker default credentials - admin, admin
                self.__rabbit_mq_username,
                self.__rabbit_mq_password
            ),
            # TODO: The heartbeat should not be disabled (0)!
            # This is a temporal solution before using threads to handle tasks
            # Notes to myself:
            # Check here:
            # https://stackoverflow.com/questions/51752890/how-to-disable-heartbeats-with-pika-and-rabbitmq
            # Check here:
            # https://github.com/pika/pika/blob/0.12.0/examples/basic_consumer_threaded.py
            heartbeat=0
        )

        return connection_parameters

    # Create a channel and bind an exchanger agent to it
    # The exchanger agent is responsible to transfer
    # messages based on the exchange type
    def create_channel(self, exchange, exchange_type):
        # Creating a new channel overwrites the existing channel
        # In case more channels have to be created, then
        # a list with channels should be created.
        # TODO: Support more channels
        if self.__connection.is_open:
            self.channel = self.__connection.channel()
            self.channel.exchange_declare(exchange=exchange,
                                          exchange_type=exchange_type)
        else:
            print("MessageExchanger>create_channel(): Error, connection is closed!")

    def configure_default_queues(self):
        # Declare the queue to which the Producer (Server) pushes data
        self.declare_queue(DEFAULT_QSB)
        # Bind the queue to the Exchanger agent
        self.bind_queue(DEFAULT_QSB)

    # The Operandi server declares the QUEUE_S_TO_B to publish to the Broker
    def declare_queue(self, queue_name, durability=False):
        if self.__connection.is_open and self.channel.is_open:
            self.channel.queue_declare(queue=queue_name, durable=durability)
        else:
            print("MessageExchanger>declare_queue(): Error, connection is closed!")

    # The Operandi server binds the QUEUE_S_TO_B to the Exchanger agent
    def bind_queue(self, queue, exchange=EXCHANGER):
        if self.__connection.is_open and self.channel.is_open:
            self.channel.queue_bind(queue=queue, exchange=exchange)
        else:
            print("MessageExchanger>bind_queue(): Error, connection is closed!")

    def send_to_queue(self, queue_name, message, exchange=EXCHANGER, durable=False):
        if durable:
            delivery_mode = pika.spec.PERSISTENT_DELIVERY_MODE
        else:
            delivery_mode = pika.spec.TRANSIENT_DELIVERY_MODE

        message_properties = pika.BasicProperties(
            delivery_mode=delivery_mode
        )

        # Publishes through the default channel
        # In case more channels have to be created, then
        # a list with channels should be created and the
        # right channel found first.
        # TODO: Support more channels
        self.channel.basic_publish(exchange=exchange,
                                   routing_key=queue_name,
                                   body=message,
                                   properties=message_properties,
                                   mandatory=True)

    # The 'callback' is the function to be called
    # when receiving from the respective queue
    def receive_from_queue(self, queue_name, callback, auto_ack=True):
        # Receives from the default channel
        # In case more channels have to be created, then
        # a list with channels should be created and the
        # right channel found first.
        # TODO: Support more channels
        self.channel.basic_consume(queue=queue_name,
                                   on_message_callback=callback,
                                   auto_ack=auto_ack)
