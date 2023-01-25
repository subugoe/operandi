import click
from time import sleep

from .broker import ServiceBroker
from .constants import (
    DEFAULT_QUEUE_SERVER_TO_BROKER,
    HPC_HOST,
    HPC_KEY_PATH,
    HPC_USERNAME
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
@click.option('--rmq-host', default="localhost", help='The host of the RabbitMQ.')
@click.option('--rmq-port', default="5672", help='The port of the RabbitMQ.')
@click.option('--rmq-vhost', default="/", help='The vhost of the RabbitMQ.')
@click.option('--hpc-host', default=HPC_HOST, help='The host of the HPC.')
@click.option('--hpc-username', default=HPC_USERNAME, help='The username used to login to the HPC.')
@click.option('--hpc-key-path', default=HPC_KEY_PATH, help='The path of the key file used for authentication.')
@click.option('-m', '--mocked', is_flag=True, default=False, help='Toggle between HPC and Local execution')
def start_broker(rmq_host, rmq_port, rmq_vhost, hpc_host, hpc_username, hpc_key_path, mocked):
    service_broker = ServiceBroker(
        rmq_host=rmq_host,
        rmq_port=rmq_port,
        rmq_vhost=rmq_vhost,
        hpc_host=hpc_host,
        hpc_username=hpc_username,
        hpc_key_path=hpc_key_path
    )

    # A list of queues for which a worker process should be created
    queues = [
        DEFAULT_QUEUE_SERVER_TO_BROKER,
        DEFAULT_QUEUE_SERVER_TO_BROKER
    ]
    for queue_name in queues:
        service_broker.log.info(f"Creating a worker processes to consume from queue: {queue_name}")
        service_broker.create_worker_process(queue_name)

    try:
        # Sleep the parent process till a signal is invoked
        # Better than sleeping in loop, not tested yet
        # signal.pause()

        # Loop and sleep
        while True:
            sleep(5)
    # TODO: Check this in docker environment
    # This may not work with SSH/Docker, SIGINT may not be caught with KeyboardInterrupt.
    except KeyboardInterrupt:
        service_broker.log.info(f"SIGINT signal received. Sending SIGINT to worker processes.")
        # Sends SIGINT to workers
        service_broker.kill_workers()
        service_broker.log.info(f"Closing gracefully in 3 seconds!")
        sleep(3)
        exit(0)
