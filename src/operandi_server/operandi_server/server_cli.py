import click
from os import environ
import uvicorn

from .constants import (
    LOG_FILE_PATH,
    LOG_LEVEL,
    SERVER_HOST as HOST,
    SERVER_PORT as PORT,
)
from .logging import reconfigure_all_loggers
from .server import OperandiServer

__all__ = ['cli']


# ----------------------------------------------------------------------
# operandi-server
# ----------------------------------------------------------------------
@click.group()
@click.version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Operandi Server
    """


@cli.command('start')
@click.option('--host', default=HOST, help='The host of the Operandi Server.')
@click.option('--port', default=PORT, help='The port of the Operandi Server.')
def start_server(host, port):
    server_url = f'http://{host}:{port}'
    db_url = environ.get("OPERANDI_URL_DB")
    # TODO: Currently, this URL consists of only host, port, and vhost
    #  Ideally, this should be extended to support the full URL
    rabbitmq_url = environ.get("OPERANDI_URL_RABBITMQ_SERVER")
    splits = rabbitmq_url.split(":")
    if len(splits) != 2:
        raise ValueError(f"Wrong RabbitMQ URL: {rabbitmq_url}")
    rmq_host = splits[0]
    rmq_port = splits[1]

    operandi_server = OperandiServer(
        host=host,
        port=port,
        server_url=server_url,
        db_url=db_url,
        rmq_host=rmq_host,
        rmq_port=rmq_port,
        rmq_vhost='/'
    )

    # Reconfigure all loggers to the same format
    reconfigure_all_loggers(
        log_level=LOG_LEVEL,
        log_file_path=LOG_FILE_PATH
    )

    uvicorn.run(
        operandi_server.app,
        host=operandi_server.host,
        port=operandi_server.port,
        log_config=None  # Disable log configuration overwriting
    )
