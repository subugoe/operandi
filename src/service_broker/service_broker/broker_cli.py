import click

from priority_queue.constants import (
    RABBIT_MQ_HOST,
    RABBIT_MQ_PORT
)
from .broker import ServiceBroker
from .constants import (
    HPC_HOST,
    HPC_USERNAME,
    HPC_KEY_PATH
)

__all__ = ['cli']


# ----------------------------------------------------------------------
# operandi-broker
# ----------------------------------------------------------------------
@click.group()
@click.version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Operandi Broker
    """


@cli.command('start')
@click.option('--rabbit-mq-host',
              default=RABBIT_MQ_HOST,
              help='The host of the RabbitMQ.')
@click.option('--rabbit-mq-port',
              default=RABBIT_MQ_PORT,
              help='The port of the RabbitMQ.')
@click.option('--hpc-host',
              default=HPC_HOST,
              help='The host of the HPC.')
@click.option('-l', '--hpc-username',
              default=HPC_USERNAME,
              help='The username used to login to the HPC.')
@click.option('-i', '--hpc-key-path',
              default=HPC_KEY_PATH,
              help='The path of the key file used for authentication.')
@click.option('-m', '--mocked',
              is_flag=True,
              default=False,
              help='Toggle between HPC and Local execution')
def start_broker(rabbit_mq_host,
                 rabbit_mq_port,
                 hpc_host,
                 hpc_username,
                 hpc_key_path,
                 use_broker_mockup):
    service_broker = ServiceBroker(rabbit_mq_host=rabbit_mq_host,
                                   rabbit_mq_port=rabbit_mq_port,
                                   hpc_host=hpc_host,
                                   hpc_username=hpc_username,
                                   hpc_key_path=hpc_key_path,
                                   use_broker_mockup=use_broker_mockup)
    print(f"INFO: Waiting for messages. To exit press CTRL+C.")
    service_broker.start()

# NOTE: Stop mechanism is not needed
# The service broker could be simply stopped with a signal (CTRL+N)
