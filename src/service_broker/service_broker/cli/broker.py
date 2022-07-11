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
def start_broker():
    service_broker = ServiceBroker()
    print(f"INFO: Waiting for messages. To exit press CTRL+C.")
    service_broker.start()

# NOTE: Stop mechanism is not needed
# The service broker could be simply stopped with a signal (CTRL+N)
