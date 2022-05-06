
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
        self.consumer.set_callback(callback)

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
service_broker.consumer.start_consuming()
