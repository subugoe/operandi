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

@click.group("server")
def server_cli():
  """
  Server related cli
  """
  print("Server related cli")


@server_cli.command('start')
@click.option('-h', '--host', default=HOST, help='The host of the Operandi server.')
@click.option('-p', '--port', default=PORT, help='The port of the Operandi server.')
def start_server(host, port):
  operandi_server = OperandiServer(host=host, port=port)
  uvicorn.run(operandi_server.app, 
              host=operandi_server.host, 
              port=operandi_server.port)

@server_cli.command('stop')
def stop_server():
  print(f"Stopped server.")

