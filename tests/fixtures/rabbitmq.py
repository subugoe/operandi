from pytest import fixture
import pika.credentials
from operandi_utils.validators import verify_and_parse_mq_uri
from operandi_utils.rabbitmq import (
    RMQConnector,
    RMQConsumer,
    RMQPublisher
)
from tests.constants import (
    OPERANDI_RABBITMQ_URL,
    OPERANDI_RABBITMQ_EXCHANGE_NAME,
    OPERANDI_RABBITMQ_EXCHANGE_ROUTER,
    OPERANDI_RABBITMQ_QUEUE_DEFAULT
)


@fixture(scope="session", name='rabbitmq_defaults')
def fixture_configure_exchange_and_queue():
    rmq_data = verify_and_parse_mq_uri(OPERANDI_RABBITMQ_URL)
    rmq_username = rmq_data["username"]
    rmq_password = rmq_data["password"]
    rmq_host = rmq_data["host"]
    rmq_port = rmq_data["port"]
    rmq_vhost = rmq_data["vhost"]

    credentials = pika.credentials.PlainCredentials(rmq_username, rmq_password)
    temp_connection = RMQConnector.open_blocking_connection(
        credentials=credentials,
        host=rmq_host,
        port=rmq_port,
        vhost=rmq_vhost
    )
    temp_channel = RMQConnector.open_blocking_channel(temp_connection)
    RMQConnector.exchange_declare(
        channel=temp_channel,
        exchange_name=OPERANDI_RABBITMQ_EXCHANGE_NAME,
        exchange_type="direct",
        durable=False
    )
    RMQConnector.queue_declare(
        channel=temp_channel,
        queue_name=OPERANDI_RABBITMQ_QUEUE_DEFAULT,
        durable=False
    )
    RMQConnector.queue_bind(
        channel=temp_channel,
        exchange_name=OPERANDI_RABBITMQ_EXCHANGE_NAME,
        queue_name=OPERANDI_RABBITMQ_QUEUE_DEFAULT,
        routing_key=OPERANDI_RABBITMQ_EXCHANGE_ROUTER
    )
    # Clean all messages inside if any from previous tests
    RMQConnector.queue_purge(
        channel=temp_channel,
        queue_name=OPERANDI_RABBITMQ_QUEUE_DEFAULT
    )


@fixture(name='rabbitmq_publisher')
def fixture_rabbitmq_publisher(rabbitmq_defaults):
    rmq_data = verify_and_parse_mq_uri(OPERANDI_RABBITMQ_URL)
    rmq_username = rmq_data["username"]
    rmq_password = rmq_data["password"]
    rmq_host = rmq_data["host"]
    rmq_port = rmq_data["port"]
    rmq_vhost = rmq_data["vhost"]

    publisher = RMQPublisher(host=rmq_host, port=rmq_port, vhost=rmq_vhost)
    publisher.authenticate_and_connect(rmq_username, rmq_password)
    publisher.enable_delivery_confirmations()
    yield publisher


@fixture(name='rabbitmq_consumer')
def fixture_rabbitmq_consumer(rabbitmq_defaults):
    rmq_data = verify_and_parse_mq_uri(OPERANDI_RABBITMQ_URL)
    rmq_username = rmq_data["username"]
    rmq_password = rmq_data["password"]
    rmq_host = rmq_data["host"]
    rmq_port = rmq_data["port"]
    rmq_vhost = rmq_data["vhost"]

    consumer = RMQConsumer(host=rmq_host, port=rmq_port, vhost=rmq_vhost)
    consumer.authenticate_and_connect(rmq_username, rmq_password)
    yield consumer
