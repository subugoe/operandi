from pkg_resources import resource_filename
#import tomli
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


__all__ = [
    "RABBIT_MQ_HOST",
    "RABBIT_MQ_PORT",
    "DEFAULT_EXCHANGER_NAME",
    "DEFAULT_EXCHANGER_TYPE",
    "DEFAULT_QUEUE_SERVER_TO_BROKER",
]

TOML_FILENAME: str = resource_filename(__name__, 'config.toml')
TOML_FD = open(TOML_FILENAME, mode='rb')
#TOML_CONFIG = tomli.load(TOML_FD)
TOML_CONFIG = tomllib.load(TOML_FD)
TOML_FD.close()

# "rabbit-mq-host" when Dockerized
# check the docker-compose.yml file
RABBIT_MQ_HOST: str = TOML_CONFIG["rabbit_mq_host"]
# This is the default port on which the RabbitMQ instance
# is running after installation, do not change it unless you know how to configure it properly.
# Pika Python client must use the same port to be able to communicate with the RabbitMQ
RABBIT_MQ_PORT: int = TOML_CONFIG["rabbit_mq_port"]

DEFAULT_EXCHANGER_NAME: str = TOML_CONFIG["default_exchange_name"]
DEFAULT_EXCHANGER_TYPE: str = TOML_CONFIG["default_exchange_type"]
DEFAULT_QUEUE_SERVER_TO_BROKER: str = TOML_CONFIG["default_queue_server_to_broker"]

# NOTE
# Make sure RabbitMQ is enabled and running on 5672 and 25672:
# $ sudo lsof -i -P -n | grep LISTEN

# if not running - enable and start it:
# $ sudo systemctl enable rabbitmq-server
# $ sudo systemctl start rabbitmq-server

# If the rabbitmq management is not running on port 15672
# Enable it:
# sudo rabbitmq-plugins enable rabbitmq_management

# For more advanced networking options:
# check here: https://www.rabbitmq.com/configure.html
# check here: https://www.rabbitmq.com/networking.html
