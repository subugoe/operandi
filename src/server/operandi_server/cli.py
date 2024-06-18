from click import group, option, version_option
from os import environ
from operandi_utils.validators import DatabaseParamType, QueueServerParamType
from operandi_server.server import OperandiServer

__all__ = ["cli"]


@group()
@version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Operandi Server
    """


@cli.command("start")
@option(
    "--local_url",
    default=environ.get("OPERANDI_SERVER_URL_LOCAL"),
    help="The local url of the Operandi Server."
)
@option(
    "--live_url",
    default=environ.get("OPERANDI_SERVER_URL_LIVE"),
    help="The live url of the Operandi Server."
)
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
def start_server(local_url: str, live_url: str, queue: str, database: str):
    operandi_server = OperandiServer(
        local_server_url=local_url, live_server_url=live_url, db_url=database, rabbitmq_url=queue)
    operandi_server.run_server()
