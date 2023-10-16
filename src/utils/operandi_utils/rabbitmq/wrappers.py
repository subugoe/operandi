from os import environ
from operandi_utils import verify_and_parse_mq_uri
from operandi_utils.rabbitmq.consumer import RMQConsumer
from operandi_utils.rabbitmq.publisher import RMQPublisher


def get_connection_consumer(
        rabbitmq_url: str = environ.get("OPERANDI_RABBITMQ_URL")
) -> RMQConsumer:
    rmq_data = verify_and_parse_mq_uri(rabbitmq_url)
    rmq_consumer = RMQConsumer(
        host=rmq_data["host"],
        port=rmq_data["port"],
        vhost=rmq_data["vhost"]
    )
    rmq_consumer.authenticate_and_connect(
        username=rmq_data["username"],
        password=rmq_data["password"]
    )
    return rmq_consumer


def get_connection_publisher(
        rabbitmq_url: str = environ.get("OPERANDI_RABBITMQ_URL"),
        enable_acks: bool = True
) -> RMQPublisher:
    rmq_data = verify_and_parse_mq_uri(rabbitmq_url)
    rmq_publisher = RMQPublisher(
        host=rmq_data["host"],
        port=rmq_data["port"],
        vhost=rmq_data["vhost"]
    )
    rmq_publisher.authenticate_and_connect(
        username=rmq_data["username"],
        password=rmq_data["password"]
    )
    if enable_acks:
        rmq_publisher.enable_delivery_confirmations()
    return rmq_publisher
