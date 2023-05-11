import click
from os import environ
import uvicorn

from operandi_utils import reconfigure_all_loggers
from .constants import LOG_FILE_PATH, LOG_LEVEL
from .server import OperandiServer

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
def start_server(host, port):
    local_server_url = environ.get("OPERANDI_LOCAL_SERVER_URL", f"http://{host}:{port}")
    live_server_url = environ.get("OPERANDI_LIVE_SERVER_URL", local_server_url)
    db_url = environ.get("OCRD_WEBAPI_DB_URL", None)
    if not db_url:
        raise ValueError("The MongoDB URL is not set! Set the environment variable OCRD_WEBAPI_DB_URL")

    # TODO: Currently, this URL consists of only host, port, and vhost
    #  Ideally, this should be extended to support the full URL
    rabbitmq_url = environ.get("OPERANDI_URL_RABBITMQ_SERVER", None)
    if not rabbitmq_url:
        raise ValueError("The RabbitMQ Server URL is not set! Set the environment variable OPERANDI_URL_RABBITMQ_SERVER")

    splits = rabbitmq_url.split(":")
    if len(splits) != 2:
        raise ValueError(f"Wrong RabbitMQ URL: {rabbitmq_url}")
    rmq_host = splits[0]
    rmq_port = splits[1]

    operandi_server = OperandiServer(
        local_server_url=local_server_url,
        live_server_url=live_server_url,
        db_url=db_url,
        rmq_host=rmq_host,
        rmq_port=rmq_port
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
