import click
import uvicorn

from .constants import (
    DB_URL,
    DEFAULT_QUEUE_SERVER_TO_BROKER,
    SERVER_HOST as HOST,
    SERVER_PORT as PORT,
)
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
@click.option('--db-url', default=DB_URL, help='The URL of the MongoDB.')
@click.option('--rmq-host', default="localhost", help='The host of the RabbitMQ Server.')
@click.option('--rmq-port', default="5672", help='The port of the RabbitMQ Server.')
@click.option('--rmq-vhost', default="/", help='The virtual host of the RabbitMQ Server.')
def start_server(host, port, db_url, rmq_host, rmq_port, rmq_vhost):
    server_url = f'http://{host}:{port}'
    operandi_server = OperandiServer(
        host=host,
        port=port,
        server_url=server_url,
        db_url=db_url,
        rmq_host=rmq_host,
        rmq_port=rmq_port,
        rmq_vhost=rmq_vhost
    )
    operandi_server.connect_publisher(
        username="default-publisher",
        password="default-publisher",
        enable_acks=True
    )
    # Create the queue to which the Operandi Server pushes messages
    operandi_server.rmq_publisher.create_queue(
        queue_name=DEFAULT_QUEUE_SERVER_TO_BROKER
    )
    uvicorn.run(
        operandi_server.app,
        host=operandi_server.host,
        port=operandi_server.port
    )
