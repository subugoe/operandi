import click
from os import environ
from time import sleep

import operandi_utils.database.database as db
from operandi_utils import reconfigure_all_loggers
from operandi_utils.rabbitmq import (
    DEFAULT_QUEUE_FOR_HARVESTER,
    DEFAULT_QUEUE_FOR_USERS
)

from operandi_utils.validators import (
    DatabaseParamType,
    QueueServerParamType
)
from .broker import ServiceBroker
from .constants import LOG_LEVEL_BROKER, LOG_FILE_PATH_BROKER


__all__ = ['cli']


@click.group()
@click.version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Operandi Broker
    """


@cli.command('start')
@click.option('-q', '--queue',
              default=environ.get(
                  "OPERANDI_URL_RABBITMQ_SERVER",
                  "amqp://localhost:5672/"
              ),
              help='The URL of the RabbitMQ Server, format: amqp://username:password@host:port/vhost',
              type=QueueServerParamType())
@click.option('-d', '--database',
              default=environ.get(
                  "OCRD_WEBAPI_DB_URL",
                  "mongodb://localhost:27018"
              ),
              help='The URL of the MongoDB, format: mongodb://host:port',
              type=DatabaseParamType())
def start_broker(queue: str, database: str):
    service_broker = ServiceBroker(
        db_url=database,
        rabbitmq_url=queue
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

    # Reconfigure all loggers to the same format
    reconfigure_all_loggers(
        log_level=LOG_LEVEL_BROKER,
        log_file_path=LOG_FILE_PATH_BROKER
    )

    try:
        db.sync_initiate_database(database)

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
