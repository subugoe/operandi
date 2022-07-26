import click
from ..service_broker import ServiceBroker
from priority_queue.constants import (
    RABBIT_MQ_HOST,
    RABBIT_MQ_PORT
)
from ..constants import (
    HPC_HOST,
    HPC_USERNAME,
    HPC_KEY_PATH
)
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
@click.option('--hpc-host',
              default=HPC_HOST,
              help='The host of the HPC.')
@click.option('-l', '--hpc-username',
              default=HPC_USERNAME,
              help='The username used to login to the HPC.')
@click.option('-i', '--hpc-key-path',
              default=HPC_KEY_PATH,
              help='The path of the key file used for authentication.')
def start_broker(rabbit_mq_host,
                 rabbit_mq_port,
                 hpc_host,
                 hpc_username,
                 hpc_key_path):
    service_broker = ServiceBroker(rabbit_mq_host=rabbit_mq_host,
                                   rabbit_mq_port=rabbit_mq_port,
                                   hpc_host=hpc_host,
                                   hpc_username=hpc_username,
                                   hpc_key_path=hpc_key_path)
    print(f"INFO: Waiting for messages. To exit press CTRL+C.")
    service_broker.start()

# NOTE: Stop mechanism is not needed
# The service broker could be simply stopped with a signal (CTRL+N)
