import click

from ..service_broker import ServiceBroker

# ----------------------------------------------------------------------
# operandi-broker broker
# ----------------------------------------------------------------------


@click.group("broker")
def broker_cli():
  """
  Broker related cli
  """


@broker_cli.command('start')
@click.option('-l', '--limit', default=1, help='The amount of mets files to be taken from the RabbitMQ.')
def start_broker(limit):
  service_broker = ServiceBroker()
  print(f"Service broker started with limit:{limit}")
  service_broker.start_consuming(limit)

@broker_cli.command('stop')
def stop_server():
  print(f"Stopped broker.")

