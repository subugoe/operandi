from click import group, option, version_option
from os import environ

from operandi_utils.validators import DatabaseParamType, QueueServerParamType
from .broker import ServiceBroker

__all__ = ["cli"]


@group()
@version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Operandi Broker
    """


@cli.command("start")
@option(
    "-q", "--queue",
    default=environ.get("OPERANDI_RABBITMQ_URL"),
    help="The URL of the RabbitMQ Server, format: amqp://username:password@host:port/vhost",
    type=QueueServerParamType()
)
@option(
    "-d", "--database",
    default=environ.get("OPERANDI_DB_URL"),
    help="The URL of the MongoDB, format: mongodb://host:port",
    type=DatabaseParamType()
)
def start_broker(queue: str, database: str):
    service_broker = ServiceBroker(db_url=database, rabbitmq_url=queue)
    service_broker.run_broker()
