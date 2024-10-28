from pika import BasicProperties
from pickle import dumps, loads
from operandi_utils.rabbitmq.constants import DEFAULT_EXCHANGER_NAME, RABBITMQ_QUEUE_DEFAULT

APP_ID = "webapi-processing-broker"
MESSAGE_1 = "RabbitMQ test 123"
MESSAGE_2 = "RabbitMQ test 456"
TEST_WORKFLOW_ID = "Test_workflow_id"
TEST_WORKSPACE_ID = "Test_workspace_id"
TEST_JOB_ID = "Test_job_id"


# NOTE: RabbitMQ docker container must be running before starting the tests
def test_publish_2_messages_to_rabbitmq(rabbitmq_publisher):
    test_headers = {"Test Header": "Test Value"}
    test_properties = BasicProperties(app_id=APP_ID, content_type="application/json", headers=test_headers)
    rabbitmq_publisher.publish_to_queue(
        queue_name=RABBITMQ_QUEUE_DEFAULT,
        message=MESSAGE_1, exchange_name=DEFAULT_EXCHANGER_NAME, properties=test_properties)
    rabbitmq_publisher.publish_to_queue(
        queue_name=RABBITMQ_QUEUE_DEFAULT,
        message=MESSAGE_2, exchange_name=DEFAULT_EXCHANGER_NAME, properties=test_properties)
    assert rabbitmq_publisher.message_counter == 2


def test_consume_2_messages_from_rabbitmq(rabbitmq_consumer):
    # Consume the 1st message
    method_frame, header_frame, message = rabbitmq_consumer.get_one_message(
        queue_name=RABBITMQ_QUEUE_DEFAULT, auto_ack=True)
    assert method_frame.delivery_tag == 1  # 1st delivered message to this queue
    assert method_frame.message_count == 1  # messages left in the queue
    assert method_frame.redelivered is False
    assert method_frame.exchange == DEFAULT_EXCHANGER_NAME
    assert method_frame.routing_key == RABBITMQ_QUEUE_DEFAULT
    # It's possible to assert header_frame the same way
    assert message.decode() == MESSAGE_1

    # Consume the 2nd message
    method_frame, header_frame, message = rabbitmq_consumer.get_one_message(
        queue_name=RABBITMQ_QUEUE_DEFAULT, auto_ack=True)
    assert method_frame.delivery_tag == 2  # 2nd delivered message to this queue
    assert method_frame.message_count == 0  # messages left in the queue
    assert method_frame.redelivered is False
    assert method_frame.exchange == DEFAULT_EXCHANGER_NAME
    assert method_frame.routing_key == RABBITMQ_QUEUE_DEFAULT
    # It's possible to assert header_frame the same way
    assert message.decode() == MESSAGE_2


def test_publish_ocrd_message_to_rabbitmq(rabbitmq_publisher):
    ocrd_processing_message = {
        "job_id": TEST_JOB_ID, "workflow_id": TEST_WORKFLOW_ID, "workspace_id": TEST_WORKSPACE_ID
    }
    message_bytes = dumps(ocrd_processing_message)
    rabbitmq_publisher.publish_to_queue(
        queue_name=RABBITMQ_QUEUE_DEFAULT, message=message_bytes, exchange_name=DEFAULT_EXCHANGER_NAME, properties=None)


def test_consume_ocrd_message_from_rabbitmq(rabbitmq_consumer):
    method_frame, header_frame, message = rabbitmq_consumer.get_one_message(
        queue_name=RABBITMQ_QUEUE_DEFAULT, auto_ack=True)
    assert method_frame.message_count == 0  # messages left in the queue
    decoded_message = loads(message)
    assert decoded_message["job_id"] == TEST_JOB_ID
    assert decoded_message["workflow_id"] == TEST_WORKFLOW_ID
    assert decoded_message["workspace_id"] == TEST_WORKSPACE_ID
