import click
from os import environ
import uvicorn

from operandi_utils import reconfigure_all_loggers
from operandi_utils.validators import (
    DatabaseParamType,
    QueueServerParamType
)
from operandi_server.constants import LOG_FILE_PATH, LOG_LEVEL
from operandi_server.server import OperandiServer

__all__ = ['cli']


@click.group()
@click.version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Operandi Server
    """


@cli.command('start')
@click.option('--host', default="localhost", help='The host of the Operandi Server.')
@click.option('--port', default="8000", help='The port of the Operandi Server.')
@click.option('-q', '--queue',
              default=environ.get(
                  "OPERANDI_URL_RABBITMQ_SERVER",
                  "amqp://localhost:5672/"
              ),
              help='The URL of the RabbitMQ Server, format: amqp://username:password@host:port/vhost',
              type=QueueServerParamType())
@click.option('-d', '--database',
              default=environ.get(
                  "OCRD_WEBAPI_DB_URL",
                  "mongodb://localhost:27018"
              ),
              help='The URL of the MongoDB, format: mongodb://host:port',
              type=DatabaseParamType())
def start_server(host, port, queue: str, database: str):
    local_server_url = environ.get("OPERANDI_LOCAL_SERVER_URL", f"http://{host}:{port}")
    live_server_url = environ.get("OPERANDI_LIVE_SERVER_URL", local_server_url)
    operandi_server = OperandiServer(
        local_server_url=local_server_url,
        live_server_url=live_server_url,
        db_url=database,
        rabbitmq_url=queue
    )

    # Reconfigure all loggers to the same format
    reconfigure_all_loggers(
        log_level=LOG_LEVEL,
        log_file_path=LOG_FILE_PATH
    )

    uvicorn.run(
        operandi_server,
        host=host,
        port=int(port),
        log_config=None  # Disable log configuration overwriting
    )
