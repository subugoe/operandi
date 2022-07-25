import click

import uvicorn

# ----------------------------------------------------------------------
# operandi-server server
# ----------------------------------------------------------------------

from ..constants import (
    SERVER_HOST as HOST,
    SERVER_PORT as PORT,
    SERVER_PATH,
    PRESERVE_REQUESTS,
)

from ..operandi_server import OperandiServer
from priority_queue.constants import RABBIT_MQ_HOST, RABBIT_MQ_PORT


@click.group("server")
def server_cli():
    """
    Server related cli
    """
    print("Server related cli")


@server_cli.command('start')
@click.option('-h', '--host',
              default=HOST,
              help='The host of the Operandi server.')
@click.option('-p', '--port',
              default=PORT,
              help='The port of the Operandi server.')
@click.option('--rabbit-mq-host',
              default=RABBIT_MQ_HOST,
              help='The host of the RabbitMQ.')
@click.option('--rabbit-mq-port',
              default=RABBIT_MQ_PORT,
              help='The port of the RabbitMQ.')
def start_server(host, port, rabbit_mq_host, rabbit_mq_port):
    operandi_server = OperandiServer(host=host,
                                     port=port,
                                     rabbit_mq_host=rabbit_mq_host,
                                     rabbit_mq_port=rabbit_mq_port)
    uvicorn.run(operandi_server.app,
                host=operandi_server.host,
                port=operandi_server.port)
