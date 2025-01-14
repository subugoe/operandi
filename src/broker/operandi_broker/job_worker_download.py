from typing_extensions import override
from operandi_broker.job_worker_base import JobWorkerBase


# TODO: Adapt the JobWorkerDownload to do the task of downloading instead of the job status worker
class JobWorkerDownload(JobWorkerBase):
    def __init__(self, db_url, rabbitmq_url, queue_name, test_sbatch=False):
        super().__init__(db_url, rabbitmq_url, queue_name)
        self.test_sbatch = test_sbatch
        self.current_message_job_id = None

    @override
    def _consumed_msg_callback(self, ch, method, properties, body):
        pass

    @override
    def _handle_msg_failure(self, interruption: bool):
        pass
