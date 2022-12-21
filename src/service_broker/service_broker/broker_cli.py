import click
import time
from os import (
    fork,
    getpid,
    getppid,
    kill,
    setsid
)
import signal
import sys

from rabbit_mq_utils.constants import (
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
                 mocked):
    service_broker = ServiceBroker(rabbit_mq_host=rabbit_mq_host,
                                   rabbit_mq_port=rabbit_mq_port,
                                   hpc_host=hpc_host,
                                   hpc_username=hpc_username,
                                   hpc_key_path=hpc_key_path,
                                   local_execution=mocked)

    child1_pid = create_child_process(service_broker, tag='server-to-broker')
    time.sleep(1)
    child2_pid = create_child_process(service_broker, tag='harvester-to-broker')
    try:
        # Sleep the parent process till
        # a CTRL+C signal is received
        # signal.pause()
        while True:
            # Sleep the parent process
            time.sleep(3)
    # TODO: This won't work with SSH/Docker, a proper SIGINT handler required
    except KeyboardInterrupt:
        print(f"INFO: CTRL+C detected. Sending SIGINT to child processes.")
        time.sleep(1)
        kill(child1_pid, signal.SIGINT)
        time.sleep(1)
        kill(child2_pid, signal.SIGINT)
        time.sleep(3)
        print(f"INFO: {getpid()}: Closing Service Broker gracefully in 3 seconds!")
        time.sleep(3)
        sys.exit(0)


# TODO: Refactor and refine things
#  time.sleep() method is used for a synchronized output during development
#  However, the flow itself does not depend on any timers!
def create_child_process(broker_instance: ServiceBroker, tag):
    # TODO: OSError will be raised if something goes wrong
    #  handle this properly
    pid = fork()
    if pid > 0:
        print(f"INFO: {getpid()}: Created child process with PID: {pid}")
    else:
        print(f"INFO: {getpid()}: I am a child process, about to listen on queue: {tag}")
        print(f"INFO: {getpid()}: My parent has PID: {getppid()}")
        try:
            setsid()  # run in the background
            if tag == 'server-to-broker':
                # Configure signal handler
                signal.signal(signal.SIGINT, signal_handler_server_queue)
                broker_instance.start_listening_to_server_queue()
            elif tag == 'harvester-to-broker':
                # Configure signal handler
                signal.signal(signal.SIGINT, signal_handle_harvester_queue)
                broker_instance.start_listening_to_harvester_queue()
        except Exception as e:
            print(f"ERROR: {e}")
            exit(-1)
    return pid


def signal_handler_server_queue(sig, frame):
    print(f"INFO: ServerQueueHandler[{getpid()}]> SIGINT received from my parent process.")
    time.sleep(1)
    # TODO: Do the cleaning here
    print(f"INFO: {getpid()}: Closing ServerQueueHandler gracefully!")
    sys.exit(0)


def signal_handle_harvester_queue(sig, frame):
    print(f"INFO: HarvesterQueueHandler[{getpid()}]> SIGINT received from my parent process.")
    time.sleep(1)
    # TODO: Do the cleaning here
    print(f"INFO: {getpid()}: Closing HarvesterQueueHandler gracefully!")
    sys.exit(0)

# NOTE: Stop mechanism is not needed
# The service broker could be simply stopped with a signal (CTRL+N)
