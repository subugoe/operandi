__all__ = [
    "RABBIT_MQ_HOST",
    "RABBIT_MQ_PORT",
    "DEFAULT_EXCHANGER_NAME",
    "DEFAULT_EXCHANGER_TYPE",
    "DEFAULT_QUEUE_SERVER_TO_BROKER",
    "DEFAULT_QUEUE_BROKER_TO_SERVER"
]

# "rabbit-mq-host" when Dockerized
# check the docker-compose.yml file
RABBIT_MQ_HOST: str = "localhost"
# This is the default port on which the RabbitMQ instance
# is running after installation, do not change it unless you know how to configure it properly.
# Pika Python client must use the same port to be able to communicate with the RabbitMQ
RABBIT_MQ_PORT: int = 5672

DEFAULT_EXCHANGER_NAME: str = "operandi_exchanger"
DEFAULT_EXCHANGER_TYPE: str = "direct"
DEFAULT_QUEUE_SERVER_TO_BROKER = "server_to_broker"
DEFAULT_QUEUE_BROKER_TO_SERVER = "broker_to_server"

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

