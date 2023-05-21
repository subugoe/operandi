from dotenv import load_dotenv
import logging
from os import environ

__all__ = [
    'DEFAULT_EXCHANGER_NAME',
    'DEFAULT_EXCHANGER_TYPE',
    'DEFAULT_QUEUE',
    'DEFAULT_QUEUE_FOR_HARVESTER',
    'DEFAULT_QUEUE_FOR_USERS',
    'DEFAULT_ROUTER',
    'RABBIT_MQ_HOST',
    'RABBIT_MQ_PORT',
    'RABBIT_MQ_VHOST',
    'RECONNECT_WAIT',
    'RECONNECT_TRIES',
    'PREFETCH_COUNT',
    'LOG_FORMAT',
    'LOG_LEVEL'
]

load_dotenv()

DEFAULT_EXCHANGER_TYPE: str = "direct"
DEFAULT_EXCHANGER_NAME: str = environ.get("OPERANDI_RABBITMQ_EXCHANGE_NAME", "operandi_default")
DEFAULT_ROUTER: str = environ.get("OPERANDI_RABBITMQ_EXCHANGE_ROUTER", "operandi_default")

DEFAULT_QUEUE: str = environ.get("OPERANDI_RABBITMQ_QUEUE_DEFAULT", "operandi_default_queue")
DEFAULT_QUEUE_FOR_HARVESTER: str = environ.get("OPERANDI_RABBITMQ_QUEUE_HARVESTER", "operandi_queue_harvester")
DEFAULT_QUEUE_FOR_USERS: str = environ.get("OPERANDI_RABBITMQ_QUEUE_USERS", "operandi_queue_users")

# 'rabbit-mq-host' when Dockerized
RABBIT_MQ_HOST: str = 'localhost'
RABBIT_MQ_PORT: int = 5672
RABBIT_MQ_VHOST: str = '/'

# Wait seconds before next reconnect try
RECONNECT_WAIT: int = 5
# Reconnect tries before timeout
RECONNECT_TRIES: int = 3
# QOS, i.e., how many messages to consume in a single go
# Check here: https://www.rabbitmq.com/consumer-prefetch.html
PREFETCH_COUNT: int = 1

LOG_FORMAT: str = '%(levelname) -10s %(asctime)s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s'
LOG_LEVEL: int = logging.WARNING
