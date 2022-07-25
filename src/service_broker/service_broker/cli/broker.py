import click

from ..service_broker import ServiceBroker
from priority_queue.constants import RABBIT_MQ_HOST, RABBIT_MQ_PORT

# ----------------------------------------------------------------------
# operandi-broker broker
# ----------------------------------------------------------------------


@click.group("broker")
def broker_cli():
    """
  Broker related cli
  """


@broker_cli.command('start')
@click.option('--rabbit-mq-host',
              default=RABBIT_MQ_HOST,
              help='The host of the RabbitMQ.')
@click.option('--rabbit-mq-port',
              default=RABBIT_MQ_PORT,
              help='The port of the RabbitMQ.')
def start_broker(rabbit_mq_host, rabbit_mq_port):
    service_broker = ServiceBroker(rabbit_mq_host=rabbit_mq_host,
                                   rabbit_mq_port=rabbit_mq_port)
    print(f"INFO: Waiting for messages. To exit press CTRL+C.")
    service_broker.start()

# NOTE: Stop mechanism is not needed
# The service broker could be simply stopped with a signal (CTRL+N)
