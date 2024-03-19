from os import environ
from pytest import fixture
import pika.credentials
from operandi_utils.validators import verify_and_parse_mq_uri
from operandi_utils.rabbitmq import (
    DEFAULT_EXCHANGER_NAME,
    get_connection_consumer,
    get_connection_publisher,
    RABBITMQ_QUEUE_DEFAULT,
    RMQConnector
)


@fixture(scope="package", name="rabbitmq_defaults")
def fixture_configure_exchange_and_queue():
    rmq_data = verify_and_parse_mq_uri(environ.get("RABBITMQ_URL"))
    rmq_username = rmq_data["username"]
    rmq_password = rmq_data["password"]
    rmq_host = rmq_data["host"]
    rmq_port = rmq_data["port"]
    rmq_vhost = rmq_data["vhost"]

    credentials = pika.credentials.PlainCredentials(rmq_username, rmq_password)
    test_connection = RMQConnector.open_blocking_connection(
        credentials=credentials,
        host=rmq_host,
        port=rmq_port,
        vhost=rmq_vhost
    )
    test_channel = RMQConnector.open_blocking_channel(test_connection)
    RMQConnector.exchange_declare(channel=test_channel, exchange_name=DEFAULT_EXCHANGER_NAME, durable=False)
    RMQConnector.queue_declare(channel=test_channel, queue_name=RABBITMQ_QUEUE_DEFAULT, durable=False)
    RMQConnector.queue_bind(
        channel=test_channel,
        exchange_name=DEFAULT_EXCHANGER_NAME,
        queue_name=RABBITMQ_QUEUE_DEFAULT,
        routing_key=RABBITMQ_QUEUE_DEFAULT
    )
    # Clean all messages inside if any from previous tests
    RMQConnector.queue_purge(channel=test_channel, queue_name=RABBITMQ_QUEUE_DEFAULT)


@fixture(scope="package", name="rabbitmq_publisher")
def fixture_rabbitmq_publisher(rabbitmq_defaults):
    publisher = get_connection_publisher(enable_acks=True)
    yield publisher


@fixture(scope="package", name="rabbitmq_consumer")
def fixture_rabbitmq_consumer(rabbitmq_defaults):
    consumer = get_connection_consumer()
    yield consumer
