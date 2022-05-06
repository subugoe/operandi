import time

from src.priority_queue.consumer import Consumer

from constants import (
    SERVICE_BROKER_IP as IP,
    SERVICE_BROKER_PORT as PORT,
)


class ServiceBroker:
    def __init__(self,
                 host=IP,
                 port=PORT):
        print(f"Constructor: {host}:{port}")

        self.consumer = Consumer()

    def __del__(self):
        print(f"Destructor")


def callback(ch, method, properties, body):
    # print(f"INFO: ch: {ch}")
    # print(f"INFO: method: {method}")
    # print(f"INFO: properties: {properties}")
    print(f"INFO: A METS URI has been consumed: {body}")


# TODO: Implement the entire service broker
# Currently the service broker only passively consumes data from the queue
service_broker = ServiceBroker()

# To consume continuously
# service_broker.consumer.set_callback(callback)
# service_broker.consumer.start_consuming()

# Loops till there is a message inside the queue
while True:
    received = service_broker.consumer.single_consume()
    if received is not None:
        break
    print(f"Looping")
    time.sleep(2)

# Do something with the received message body
print(f"{received}")