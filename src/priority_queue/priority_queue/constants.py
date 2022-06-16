__all__ = [
  "RABBIT_MQ_HOST",
  "RABBIT_MQ_PORT",
  "RABBIT_MQ_PATH",
  "DEFAULT_EXCHANGER_NAME",
  "DEFAULT_EXCHANGER_TYPE",
  "DEFAULT_QUEUE_NAME"
]

RABBIT_MQ_HOST: str = "localhost"
# This is the default port on which the RabbitMQ instance
# is running after installation, do not change it unless you know how to configure it properly.
# Pika Python client must use the same port to be able to communicate with the RabbitMQ
RABBIT_MQ_PORT: int = 5672
RABBIT_MQ_PATH: str = f"http://{RABBIT_MQ_HOST}:{RABBIT_MQ_PORT}"

DEFAULT_EXCHANGER_NAME: str = "operandi_exchanger"
DEFAULT_EXCHANGER_TYPE: str = "direct"
DEFAULT_QUEUE_NAME: str = "basic_queue1"

# NOTE
# Make sure RabbitMQ is enabled and running on 5672 and 25672:
# $ sudo lsof -i -P -n | grep LISTEN

# if not running - enable and start it:
# $ sudo systemctl enable rabbitmq-server
# $ sudo systemctl start rabbitmq-server

# For more advanced networking options:
# check here: https://www.rabbitmq.com/configure.html
# check here: https://www.rabbitmq.com/networking.html

