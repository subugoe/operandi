import asyncio
import click
import datetime
from time import sleep
from os import environ

import ocrd_webapi.database as db
from operandi_utils import reconfigure_all_loggers

from .broker import ServiceBroker
from .constants import (
    DEFAULT_QUEUE_FOR_HARVESTER,
    DEFAULT_QUEUE_FOR_USERS,
    LOG_FOLDER_PATH,
    LOG_LEVEL,
)


__all__ = ['cli']


@click.group()
@click.version_option()
def cli(**kwargs):  # pylint: disable=unused-argument
    """
    Entry-point of multipurpose CLI for Operandi Broker
    """


@cli.command('start')
def start_broker():
    db_url = environ.get("OPERANDI_URL_DB", "mongodb://localhost:27018")
    if not db_url:
        raise ValueError("The MongoDB URL is not set! Set the environment variable OPERANDI_URL_DB")

    # TODO: Currently, this URL consists of only host, port, and vhost
    #  Ideally, this should be extended to support the full URL
    rabbitmq_url = environ.get("OPERANDI_URL_RABBITMQ_SERVER", "localhost:5672")
    if not rabbitmq_url:
        raise ValueError("The RabbitMQ Server URL is not set! Set the environment variable OPERANDI_URL_RABBITMQ_SERVER")

    splits = rabbitmq_url.split(":")
    if len(splits) != 2:
        raise ValueError(f"Wrong RabbitMQ URL: {rabbitmq_url}")
    rmq_host = splits[0]
    rmq_port = splits[1]

    service_broker = ServiceBroker(
        db_url=db_url,
        rmq_host=rmq_host,
        rmq_port=rmq_port,
        rmq_vhost='/'
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
