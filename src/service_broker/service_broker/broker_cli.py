import asyncio
import click
import datetime
from time import sleep

import ocrd_webapi.database as db

from .broker import ServiceBroker
from .constants import (
    DB_URL,
    DEFAULT_QUEUE_FOR_HARVESTER,
    DEFAULT_QUEUE_FOR_USERS,
    HPC_HOST,
    HPC_KEY_PATH,
    HPC_USERNAME,
    LOG_FOLDER_PATH,
    LOG_LEVEL,
)
from .logging import reconfigure_all_loggers

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
@click.option('--db-url', default=DB_URL, help='The URL of the MongoDB.')
@click.option('--rmq-host', default="localhost", help='The host of the RabbitMQ.')
@click.option('--rmq-port', default="5672", help='The port of the RabbitMQ.')
@click.option('--rmq-vhost', default="/", help='The vhost of the RabbitMQ.')
@click.option('--hpc-host', default=HPC_HOST, help='The host of the HPC.')
@click.option('--hpc-username', default=HPC_USERNAME, help='The username used to login to the HPC.')
@click.option('--hpc-key-path', default=HPC_KEY_PATH, help='The path of the key file used for authentication.')
def start_broker(db_url, rmq_host, rmq_port, rmq_vhost, hpc_host, hpc_username, hpc_key_path):
    service_broker = ServiceBroker(
        db_url=db_url,
        rmq_host=rmq_host,
        rmq_port=rmq_port,
        rmq_vhost=rmq_vhost,
        hpc_host=hpc_host,
        hpc_username=hpc_username,
        hpc_key_path=hpc_key_path
    )

    # A list of queues for which a worker process should be created
    queues = [
        DEFAULT_QUEUE_FOR_USERS,
        DEFAULT_QUEUE_FOR_HARVESTER
    ]
    try:
        for queue_name in queues:
            service_broker.log.info(f"Creating a worker processes to consume from queue: {queue_name}")
            service_broker.create_worker_process(queue_name)
    except Exception as error:
        service_broker.log.error(f"Error while creating worker processes: {error}")

    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    # Reconfigure all loggers to the same format
    reconfigure_all_loggers(
        log_level=LOG_LEVEL,
        log_file_path=f"{LOG_FOLDER_PATH}/broker_{current_time}.log"
    )

    try:
        loop = asyncio.get_event_loop()
        db_coroutine = db.initiate_database(db_url)
        loop.run_until_complete(db_coroutine)

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
    except Exception as error:
        # This is for logging any other errors
        service_broker.log.error(f"Unexpected error: {error}")
