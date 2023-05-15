from pytest import fixture
import pika.credentials
from operandi_utils.rabbitmq import (
    RMQConnector,
    RMQConsumer,
    RMQPublisher
)
from tests.constants import RABBITMQ_TEST_QUEUE_DEFAULT


@fixture(scope="session", name='rabbitmq_defaults')
def fixture_configure_exchange_and_queue():
    credentials = pika.credentials.PlainCredentials("test-session", "test-session")
    temp_connection = RMQConnector.open_blocking_connection(
        credentials=credentials,
        host="localhost",
        port=5672,
        vhost="test"
    )
    temp_channel = RMQConnector.open_blocking_channel(temp_connection)
    RMQConnector.exchange_declare(
        channel=temp_channel,
        exchange_name=RABBITMQ_TEST_QUEUE_DEFAULT,
        exchange_type="direct",
        durable=False
    )
    RMQConnector.queue_declare(
        channel=temp_channel,
        queue_name=RABBITMQ_TEST_QUEUE_DEFAULT,
        durable=False
    )
    RMQConnector.queue_bind(
        channel=temp_channel,
        exchange_name=RABBITMQ_TEST_QUEUE_DEFAULT,
        queue_name=RABBITMQ_TEST_QUEUE_DEFAULT,
        routing_key=RABBITMQ_TEST_QUEUE_DEFAULT
    )
    # Clean all messages inside if any from previous tests
    RMQConnector.queue_purge(
        channel=temp_channel,
        queue_name=RABBITMQ_TEST_QUEUE_DEFAULT
    )


@fixture(name='rabbitmq_publisher')
def fixture_rabbitmq_publisher(rabbitmq_defaults):
    publisher = RMQPublisher(host="localhost", port=5672, vhost="test")
    publisher.authenticate_and_connect("test-session", "test-session")
    publisher.enable_delivery_confirmations()
    yield publisher


@fixture(name='rabbitmq_consumer')
def fixture_rabbitmq_consumer(rabbitmq_defaults):
    consumer = RMQConsumer(host="localhost", port=5672, vhost="test")
    consumer.authenticate_and_connect("test-session", "test-session")
    yield consumer
