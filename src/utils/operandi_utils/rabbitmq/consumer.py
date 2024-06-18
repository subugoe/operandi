from logging import getLogger
from typing import Any, Union

from pika import PlainCredentials

from operandi_utils.constants import LOG_LEVEL_RMQ_CONSUMER
from .connector import RMQConnector
from .constants import (
    DEFAULT_EXCHANGER_NAME, DEFAULT_EXCHANGER_TYPE,
    RABBITMQ_QUEUE_JOB_STATUSES, RABBITMQ_QUEUE_HARVESTER, RABBITMQ_QUEUE_USERS
)


class RMQConsumer(RMQConnector):
    def __init__(self, host: str, port: int, vhost: str) -> None:
        self.logger = getLogger("operandi_utils.rabbitmq.consumer")
        self.logger.setLevel(LOG_LEVEL_RMQ_CONSUMER)
        super().__init__(host=host, port=port, vhost=vhost)
        self.consumer_tag = None
        self.consuming = False
        self.was_consuming = False
        self.closing = False
        self.reconnect_delay = 0

    def authenticate_and_connect(self, username: str, password: str, erase_on_connect: bool = False) -> None:
        credentials = PlainCredentials(username=username, password=password, erase_on_connect=erase_on_connect)
        self._connection = RMQConnector.open_blocking_connection(
            host=self._host, port=self._port, vhost=self._vhost, credentials=credentials)
        self._channel = RMQConnector.open_blocking_channel(self._connection)
        self.setup_defaults()
        RMQConnector.set_qos(self._channel)

    def setup_defaults(self) -> None:
        RMQConnector.declare_and_bind_defaults(self._connection, self._channel)
        self.create_queue(queue_name=RABBITMQ_QUEUE_HARVESTER)
        self.create_queue(queue_name=RABBITMQ_QUEUE_USERS)
        self.create_queue(queue_name=RABBITMQ_QUEUE_JOB_STATUSES)

    def create_queue(
        self, queue_name: str, exchange_name: str = DEFAULT_EXCHANGER_NAME, exchange_type: str = DEFAULT_EXCHANGER_TYPE,
        passive: bool = False, durable: bool = False, auto_delete: bool = False, exclusive: bool = False
    ) -> None:
        RMQConnector.exchange_declare(
            channel=self._channel, exchange_name=exchange_name, exchange_type=exchange_type, passive=False,
            durable=False, auto_delete=False, internal=False)
        RMQConnector.queue_declare(
            channel=self._channel, queue_name=queue_name, passive=passive, durable=durable, auto_delete=auto_delete,
            exclusive=exclusive)
        # the routing key matches the queue name
        RMQConnector.queue_bind(
            channel=self._channel, queue_name=queue_name, exchange_name=exchange_name, routing_key=queue_name)

    def get_one_message(self, queue_name: str, auto_ack: bool = False) -> Union[Any, None]:
        message = None
        if self._channel and self._channel.is_open:
            message = self._channel.basic_get(queue=queue_name, auto_ack=auto_ack)
        return message

    def configure_consuming(self, queue_name: str, callback_method: Any) -> None:
        self.logger.debug(f"Configuring consuming with queue: {queue_name}")
        self._channel.add_on_cancel_callback(self.__on_consumer_cancelled)
        self.consumer_tag = self._channel.basic_consume(queue_name, callback_method)
        self.was_consuming = True
        self.consuming = True

    def start_consuming(self) -> None:
        if self._channel and self._channel.is_open:
            self._channel.start_consuming()

    def get_waiting_message_count(self) -> Union[int, None]:
        if self._channel and self._channel.is_open:
            return self._channel.get_waiting_message_count()
        return None

    def __on_consumer_cancelled(self, frame: Any) -> None:
        self.logger.warning(f"The consumer was cancelled remotely in frame: {frame}")
        if self._channel:
            self._channel.close()

    def ack_message(self, delivery_tag: int) -> None:
        self.logger.debug(f"Acknowledging message {delivery_tag}")
        self._channel.basic_ack(delivery_tag)
