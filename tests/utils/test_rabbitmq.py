import pika
import pickle
from tests.constants import (
    OPERANDI_RABBITMQ_EXCHANGE_NAME,
    OPERANDI_RABBITMQ_EXCHANGE_ROUTER,
    OPERANDI_RABBITMQ_QUEUE_DEFAULT
)


# NOTE: RabbitMQ docker container must be running before starting the tests
def test_publish_message_to_rabbitmq(rabbitmq_publisher):
    test_headers = {
        'OCR-D WebApi Test Header': 'OCR-D WebApi Test Value'
    }
    test_properties = pika.BasicProperties(
        app_id='webapi-processing-broker',
        content_type='application/json',
        headers=test_headers
    )
    rabbitmq_publisher.publish_to_queue(
        queue_name=OPERANDI_RABBITMQ_QUEUE_DEFAULT,
        message="RabbitMQ test 123",
        exchange_name=OPERANDI_RABBITMQ_EXCHANGE_NAME,
        properties=test_properties
    )
    rabbitmq_publisher.publish_to_queue(
        queue_name=OPERANDI_RABBITMQ_QUEUE_DEFAULT,
        message="RabbitMQ test 456",
        exchange_name=OPERANDI_RABBITMQ_EXCHANGE_NAME,
        properties=test_properties
    )
    assert rabbitmq_publisher.message_counter == 2


def test_consume_2_messages_from_rabbitmq(rabbitmq_consumer):
    # Consume the 1st message
    method_frame, header_frame, message = rabbitmq_consumer.get_one_message(
        queue_name=OPERANDI_RABBITMQ_QUEUE_DEFAULT,
        auto_ack=True
    )
    assert method_frame.delivery_tag == 1  # 1st delivered message to this queue
    assert method_frame.message_count == 1  # messages left in the queue
    assert method_frame.redelivered is False
    assert method_frame.exchange == OPERANDI_RABBITMQ_EXCHANGE_NAME
    assert method_frame.routing_key == OPERANDI_RABBITMQ_EXCHANGE_ROUTER
    # It's possible to assert header_frame the same way
    assert message.decode() == 'RabbitMQ test 123'

    # Consume the 2nd message
    method_frame, header_frame, message = rabbitmq_consumer.get_one_message(
        queue_name=OPERANDI_RABBITMQ_QUEUE_DEFAULT,
        auto_ack=True
    )
    assert method_frame.delivery_tag == 2  # 2nd delivered message to this queue
    assert method_frame.message_count == 0  # messages left in the queue
    assert method_frame.redelivered is False
    assert method_frame.exchange == OPERANDI_RABBITMQ_EXCHANGE_NAME
    assert method_frame.routing_key == OPERANDI_RABBITMQ_EXCHANGE_ROUTER
    # It's possible to assert header_frame the same way
    assert message.decode() == 'RabbitMQ test 456'


def test_publish_ocrd_message_to_rabbitmq(rabbitmq_publisher):
    ocrd_processing_message = {
        "job_id": "Test_job_id",
        "workflow_id": "Test_workflow_id",
        "workspace_id": "Test_workspace_id"
    }
    message_bytes = pickle.dumps(ocrd_processing_message)
    rabbitmq_publisher.publish_to_queue(
        queue_name=OPERANDI_RABBITMQ_QUEUE_DEFAULT,
        message=message_bytes,
        exchange_name=OPERANDI_RABBITMQ_EXCHANGE_NAME,
        properties=None
    )


def test_consume_ocrd_message_from_rabbitmq(rabbitmq_consumer):
    method_frame, header_frame, message = rabbitmq_consumer.get_one_message(
        queue_name=OPERANDI_RABBITMQ_QUEUE_DEFAULT,
        auto_ack=True
    )
    assert method_frame.message_count == 0  # messages left in the queue
    decoded_message = pickle.loads(message)
    assert decoded_message['job_id'] == "Test_job_id"
    assert decoded_message['workflow_id'] == "Test_workflow_id"
    assert decoded_message['workspace_id'] == "Test_workspace_id"
