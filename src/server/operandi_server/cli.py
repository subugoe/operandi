import click
from os import environ
import uvicorn

from operandi_utils import reconfigure_all_loggers
from operandi_utils.constants import LOG_FILE_PATH_SERVER, LOG_LEVEL_SERVER
from operandi_utils.validators import DatabaseParamType, QueueServerParamType
from operandi_server.server import OperandiServer

__all__ = ['cli']


@click.group()
@click.version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Operandi Server
    """


@cli.command('start')
@click.option('--local_url', default="http://0.0.0.0:8000", help='The local url of the Operandi Server.')
@click.option('--live_url', default="http://localhost:8000", help='The live url of the Operandi Server.')
@click.option('-q', '--queue',
              default=environ.get("OPERANDI_RABBITMQ_URL"),
              help='The URL of the RabbitMQ Server, format: amqp://username:password@host:port/vhost',
              type=QueueServerParamType())
@click.option('-d', '--database',
              default=environ.get("OPERANDI_DB_URL"),
              help='The URL of the MongoDB, format: mongodb://host:port',
              type=DatabaseParamType())
def start_server(local_url: str, live_url: str, queue: str, database: str):
    local_server_url = environ.get("OPERANDI_SERVER_URL_LOCAL", local_url)
    live_server_url = environ.get("OPERANDI_SERVER_URL_LIVE", live_url)
    operandi_server = OperandiServer(
        local_server_url=local_server_url,
        live_server_url=live_server_url,
        db_url=database,
        rabbitmq_url=queue
    )

    host, port = local_url.split("//")[1].split(":")

    # Reconfigure all loggers to the same format
    reconfigure_all_loggers(
        log_level=LOG_LEVEL_SERVER,
        log_file_path=LOG_FILE_PATH_SERVER
    )

    uvicorn.run(
        operandi_server,
        host=host,
        port=int(port),
        log_config=None  # Disable log configuration overwriting
    )
