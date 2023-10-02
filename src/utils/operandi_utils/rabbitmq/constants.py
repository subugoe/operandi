DEFAULT_EXCHANGER_NAME: str = "operandi_default_exchange"
DEFAULT_EXCHANGER_TYPE: str = "direct"
RABBITMQ_QUEUE_DEFAULT: str = "operandi_queue_default"
RABBITMQ_QUEUE_HARVESTER: str = "operandi_queue_harvester"
RABBITMQ_QUEUE_JOB_STATUSES: str = "operandi_queue_job_statuses"
RABBITMQ_QUEUE_USERS: str = "operandi_queue_users"

# Wait seconds before next reconnect try
RECONNECT_WAIT: int = 5
# Reconnect tries before timeout
RECONNECT_TRIES: int = 3
# QOS, i.e., how many messages to consume in a single go
# Check here: https://www.rabbitmq.com/consumer-prefetch.html
PREFETCH_COUNT: int = 1
