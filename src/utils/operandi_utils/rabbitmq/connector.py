from typing import Any, Optional, Union

from pika import BasicProperties, BlockingConnection, ConnectionParameters, PlainCredentials
from pika.adapters.blocking_connection import BlockingChannel

from .constants import (
    DEFAULT_EXCHANGER_NAME, DEFAULT_EXCHANGER_TYPE, HEARTBEAT, PREFETCH_COUNT, RABBITMQ_QUEUE_DEFAULT, RECONNECT_TRIES,
    RECONNECT_WAIT
)


class RMQConnector:
    def __init__(self, host: str, port: int, vhost: str) -> None:
        self._host = host
        self._port = port
        self._vhost = vhost

        # According to the documentation, Pika blocking
        # connections are not thread-safe!
        self._connection = None
        self._channel = None

        # Should try reconnecting again
        self._try_reconnecting = False
        # If the module has been stopped with a
        # keyboard interruption, i.e., CTRL + C
        self._gracefully_stopped = False

    @staticmethod
    def declare_and_bind_defaults(connection: BlockingConnection, channel: BlockingChannel) -> None:
        if not (connection and connection.is_open):
            return
        if not (channel and channel.is_open):
            return

        RMQConnector.exchange_declare(channel=channel)  # Declare the default exchange agent
        RMQConnector.queue_declare(channel, queue_name=RABBITMQ_QUEUE_DEFAULT)  # Declare the default queue
        RMQConnector.queue_bind(
            channel, queue_name=RABBITMQ_QUEUE_DEFAULT, exchange_name=DEFAULT_EXCHANGER_NAME,
            routing_key=RABBITMQ_QUEUE_DEFAULT)  # Bind the default queue to the default exchange

    @staticmethod
    def open_blocking_connection(credentials: PlainCredentials, host: str, port: int, vhost: str) -> BlockingConnection:
        connection_params = ConnectionParameters(
            host=host, port=port, virtual_host=vhost, credentials=credentials, heartbeat=HEARTBEAT,
            connection_attempts=RECONNECT_TRIES, retry_delay=RECONNECT_WAIT
        )
        return BlockingConnection(parameters=connection_params)

    @staticmethod
    def open_blocking_channel(connection: BlockingConnection) -> Union[BlockingChannel, None]:
        if not (connection and connection.is_open):
            return
        return connection.channel()

    @staticmethod
    def exchange_bind(
        channel: BlockingChannel, destination_exchange: str, source_exchange: str, routing_key: str,
        arguments: Optional[Any] = None
    ) -> None:
        if not (channel and channel.is_open):
            return
        if arguments is None:
            arguments = {}
        channel.exchange_bind(
            destination=destination_exchange, source=source_exchange, routing_key=routing_key, arguments=arguments)

    @staticmethod
    def exchange_declare(
        channel: BlockingChannel, exchange_name: str = DEFAULT_EXCHANGER_NAME,
        exchange_type: str = DEFAULT_EXCHANGER_TYPE, passive: bool = False, durable: bool = False,
        auto_delete: bool = False, internal: bool = False, arguments: Optional[Any] = None
    ) -> None:
        if not (channel and channel.is_open):
            return
        if arguments is None:
            arguments = {}
        # Passive - only checks if the exchange exists
        # Durable - Survive a reboot of RabbitMQ Server
        # Auto Delete - Remove when no more queues are bound to it
        # Internal - Can only be published to by other exchanges
        # Arguments - Custom key/value pair arguments for the exchange
        channel.exchange_declare(
            exchange=exchange_name, exchange_type=exchange_type, passive=passive, durable=durable,
            auto_delete=auto_delete, internal=internal, arguments=arguments)

    @staticmethod
    def exchange_delete(channel: BlockingChannel, exchange_name: str, if_unused: bool = False) -> None:
        if not (channel and channel.is_open):
            return
        channel.exchange_delete(exchange=exchange_name, if_unused=if_unused)

    @staticmethod
    def exchange_unbind(
        channel: BlockingChannel, destination_exchange: str, source_exchange: str, routing_key: str,
        arguments: Optional[Any] = None
    ) -> None:
        if not (channel and channel.is_open):
            return
        if arguments is None:
            arguments = {}
        channel.exchange_unbind(
            destination=destination_exchange, source=source_exchange, routing_key=routing_key, arguments=arguments)

    @staticmethod
    def queue_bind(
        channel: BlockingChannel, queue_name: str, exchange_name: str, routing_key: str, arguments: Optional[Any] = None
    ) -> None:
        if not (channel and channel.is_open):
            return
        if arguments is None:
            arguments = {}
        channel.queue_bind(queue=queue_name, exchange=exchange_name, routing_key=routing_key, arguments=arguments)

    @staticmethod
    def queue_declare(
        channel: BlockingChannel, queue_name: str, passive: bool = False, durable: bool = False,
        exclusive: bool = False, auto_delete: bool = False, arguments: Optional[Any] = None
    ) -> None:
        if not (channel and channel.is_open):
            return
        if arguments is None:
            arguments = {}
        # Passive - only checks if the queue exists
        # Durable - Survive a reboot of RabbitMQ Server
        # Exclusive - Only allow access by the current connection
        # Auto Delete - Delete after consumer cancels or disconnects
        # Arguments - Custom key/value pair arguments for the exchange
        channel.queue_declare(
            queue=queue_name, passive=passive, durable=durable, exclusive=exclusive, auto_delete=auto_delete,
            arguments=arguments)

    @staticmethod
    def queue_delete(
        channel: BlockingChannel, queue_name: str, if_unused: bool = False, if_empty: bool = False
    ) -> None:
        if not (channel and channel.is_open):
            return
        channel.queue_delete(queue=queue_name, if_unused=if_unused, if_empty=if_empty)

    @staticmethod
    def queue_purge(channel: BlockingChannel, queue_name: str) -> None:
        if not (channel and channel.is_open):
            return
        channel.queue_purge(queue=queue_name)

    @staticmethod
    def queue_unbind(
        channel: BlockingChannel, queue_name: str, exchange_name: str, routing_key: str, arguments: Optional[Any] = None
    ) -> None:
        if not (channel and channel.is_open):
            return
        if arguments is None:
            arguments = {}
        channel.queue_unbind(queue=queue_name, exchange=exchange_name, routing_key=routing_key, arguments=arguments)

    @staticmethod
    def set_qos(
        channel: BlockingChannel, prefetch_size: int = 0, prefetch_count: int = PREFETCH_COUNT, global_qos: bool = False
    ) -> None:
        if not (channel and channel.is_open):
            return
        # Prefetch size - No specific limit if set to 0
        # Global QoS - Should the qos apply to all channels of the connection
        channel.basic_qos(prefetch_size=prefetch_size, prefetch_count=prefetch_count, global_qos=global_qos)

    @staticmethod
    def confirm_delivery(channel: BlockingChannel) -> None:
        if not (channel and channel.is_open):
            return
        channel.confirm_delivery()

    @staticmethod
    def basic_publish(
        channel: BlockingChannel, exchange_name: str, routing_key: str, message_body: bytes, properties: BasicProperties
    ) -> None:
        if not (channel and channel.is_open):
            return
        channel.basic_publish(exchange=exchange_name, routing_key=routing_key, body=message_body, properties=properties)
