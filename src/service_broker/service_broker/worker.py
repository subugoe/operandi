import datetime
import json
import logging
import signal
from os import getpid, getppid, setsid, makedirs
from os.path import dirname
import os
from sys import exit
from time import sleep

import ocrd_webapi.database as db
from ocrd_webapi.managers.nextflow_manager import NextflowManager
from ocrd_webapi.rabbitmq import RMQConsumer
from .constants import (
    LOG_FOLDER_PATH,
    LOG_LEVEL_WORKER,
    HPC_HOST,
    HPC_USERNAME,
    HPC_KEY_PATH
)

from .logging import reconfigure_all_loggers
from .hpc_connector import HPCConnector


# Each worker class listens to a specific queue,
# consume messages, and process messages.
class Worker:
    def __init__(self, db_url, rmq_host, rmq_port, rmq_vhost, queue_name, native=True):
        self.log = logging.getLogger(__name__)

        # Process ID of this worker
        self.pid = getpid()
        # Process ID of the service broker (parent)
        self.ppid = getppid()
        self.queue_name = queue_name

        self.db_url = db_url
        # Connection to RabbitMQ related parameters
        self.rmq_host = rmq_host
        self.rmq_port = rmq_port
        self.rmq_vhost = rmq_vhost
        self.rmq_username = "default-consumer"
        self.rmq_password = "default-consumer"
        self.rmq_consumer = None

        self.native = native
        self.hpc_connector = None

        # Currently consumed message related parameters
        self.current_message_delivery_tag = None
        self.current_message_ws_id = None
        self.current_message_wf_id = None
        self.current_message_job_id = None
        self.has_consumed_message = False

    def run(self):
        try:
            # Source: https://unix.stackexchange.com/questions/18166/what-are-session-leaders-in-ps
            # Make the current process session leader
            setsid()
            current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
            # Reconfigure all loggers to the same format
            reconfigure_all_loggers(
                log_level=LOG_LEVEL_WORKER,
                log_file_path=f"{LOG_FOLDER_PATH}/worker_{self.queue_name}_{current_time}.log"
            )
            self.log.info(f"Activating signal handler for SIGINT, SIGTERM")
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            db.sync_initiate_database(self.db_url)

            if not self.native:
                self.hpc_connector = HPCConnector()
                if self.hpc_connector:
                    self.hpc_connector.connect_to_hpc(HPC_HOST, HPC_USERNAME, HPC_KEY_PATH)
                    self.log.info("HPC connection successful.")
                    self.log.info("Worker runs jobs in HPC.")
                else:
                    self.log.error("HPC connection has failed.")
            else:
                self.log.info("Worker runs jobs natively.")

            self.connect_consumer()

            # Different handlers based on the worker type: native/hpc
            if self.native:
                self.configure_consuming(self.queue_name, self.__on_message_consumed_callback)
            else:
                self.configure_consuming(self.queue_name, self.__on_message_consumed_callback_hpc)

            self.start_consuming()
        except Exception as e:
            self.log.error(f"The worker failed to run, reason: {e}")
            raise Exception(f"The worker failed to run, reason: {e}")

    def connect_consumer(self):
        if self.rmq_consumer:
            # If for some reason connect_consumer() is called more than once.
            self.log.warning(f"The RMQConsumer was already instantiated. "
                             f"Overwriting the existing RMQConsumer.")
        self.log.info(f"Connecting RMQConsumer to RabbitMQ server: "
                      f"{self.rmq_host}:{self.rmq_port}{self.rmq_vhost}")
        self.rmq_consumer = RMQConsumer(host=self.rmq_host, port=self.rmq_port, vhost=self.rmq_vhost)
        # TODO: Remove this information before the release
        self.log.debug(f"RMQConsumer authenticates with username: "
                       f"{self.rmq_username}, password: {self.rmq_password}")
        self.rmq_consumer.authenticate_and_connect(username=self.rmq_username, password=self.rmq_password)
        self.log.info(f"Successfully connected RMQConsumer.")

    def configure_consuming(self, queue_name, callback_method):
        if not self.rmq_consumer:
            raise Exception("The RMQConsumer connection is not configured or broken")
        self.log.info(f"Configuring the consuming for queue: {queue_name}")
        self.rmq_consumer.configure_consuming(
            queue_name=queue_name,
            callback_method=callback_method
        )

    def start_consuming(self):
        if not self.rmq_consumer:
            raise Exception("The RMQConsumer connection is not configured or broken")
        self.log.info(f"Starting consuming from queue: {self.queue_name}")
        self.rmq_consumer.start_consuming()

    # The callback method provided to the Consumer listener
    # The arguments to this method are passed by the caller
    def __on_message_consumed_callback(self, ch, method, properties, body):
        # self.log.debug(f"ch: {ch}, method: {method}, properties: {properties}, body: {body}")
        # self.log.debug(f"Consumed message: {body}")

        self.current_message_delivery_tag = method.delivery_tag
        self.has_consumed_message = True

        # Since the workflow_message is constructed by the Operandi Server,
        # it should not fail here when parsing under normal circumstances.
        try:
            consumed_message = json.loads(body)
            self.log.info(f"Consumed message: {consumed_message}")
            self.current_message_ws_id = consumed_message["workspace_id"]
            self.current_message_wf_id = consumed_message["workflow_id"]
            self.current_message_job_id = consumed_message["job_id"]
            input_file_grp = consumed_message["input_file_grp"]
        except Exception as error:
            self.log.error(f"Parsing the consumed message has failed: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # Handle database related reads and set the workflow job status to RUNNING
        try:
            # TODO: This should be optimized, i.e., single read to the DB instead of three
            workflow_script_path = db.sync_get_workflow_script_path(self.current_message_wf_id)
            workspace_mets_path = db.sync_get_workspace_mets_path(self.current_message_ws_id)
            workspace_path = db.sync_get_workspace(self.current_message_ws_id).workspace_path
            job_dir = db.sync_get_workflow_job(self.current_message_job_id).job_path
            job_state = "RUNNING"
            self.log.info(f"Setting new job state[{job_state}] of job_id: {self.current_message_job_id}")
            db.sync_set_workflow_job_state(self.current_message_job_id, job_state=job_state)
        except Exception as error:
            self.log.error(f"Database related error has occurred: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # Trigger a Nextflow process
        try:
            nf_process = NextflowManager.execute_workflow(
                nf_script_path=workflow_script_path,
                workspace_mets_path=workspace_mets_path,
                workspace_path=workspace_path,
                job_dir=job_dir,
                in_background=False
            )
        except Exception as error:
            self.log.error(f"Triggering a nextflow process has failed: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # The worker blocks here till the nextflow process finishes

        if nf_process.returncode != 0:
            self.log.error(f"The Nextflow process exited with return code: {nf_process.returncode}")
            self.__handle_message_failure(interruption=False)
            return

        self.log.debug(f"The Nextflow process has finished successfully")
        job_state = "SUCCESS"
        self.log.info(f"Setting new state[{job_state}] of job_id: {self.current_message_job_id}")
        db.sync_set_workflow_job_state(self.current_message_job_id, job_state=job_state)
        self.has_consumed_message = False
        self.log.debug(f"Acking delivery tag: {self.current_message_delivery_tag}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __on_message_consumed_callback_hpc(self, ch, method, properties, body):
        # self.log.debug(f"ch: {ch}, method: {method}, properties: {properties}, body: {body}")
        # self.log.debug(f"Consumed message: {body}")

        self.current_message_delivery_tag = method.delivery_tag
        self.has_consumed_message = True

        # Since the workflow_message is constructed by the Operandi Server,
        # it should not fail here when parsing under normal circumstances.
        try:
            consumed_message = json.loads(body)
            self.log.info(f"Consumed message: {consumed_message}")
            self.current_message_ws_id = consumed_message["workspace_id"]
            self.current_message_wf_id = consumed_message["workflow_id"]
            self.current_message_job_id = consumed_message["job_id"]
            input_file_grp = consumed_message["input_file_grp"]
        except Exception as error:
            self.log.error(f"Parsing the consumed message has failed: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # Handle database related reads and set the workflow job status to RUNNING
        try:
            # TODO: This should be optimized, i.e., single read to the DB instead of three
            workflow_script_path = db.sync_get_workflow_script_path(self.current_message_wf_id)
            workspace_mets_path = db.sync_get_workspace_mets_path(self.current_message_ws_id)
            workspace_path = db.sync_get_workspace(self.current_message_ws_id).workspace_path
            job_dir = db.sync_get_workflow_job(self.current_message_job_id).job_path
            job_state = "RUNNING"
            self.log.info(f"Setting new job state[{job_state}] of job_id: {self.current_message_job_id}")
            db.sync_set_workflow_job_state(self.current_message_job_id, job_state=job_state)
        except Exception as error:
            self.log.error(f"Database related error has occurred: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # Trigger a slurm job in the HPC
        try:
            # TODO: Use the actual nextflow workflow script here,
            #  instead of using the nextflow_workflows/template_workflow.nf
            slurm_job_return_code = self.trigger_slurm_job(
                workspace_dir=workspace_path,
                job_dir=job_dir,
                job_id=self.current_message_job_id,
                input_file_grp=input_file_grp
            )
        except Exception as error:
            self.log.error(f"Triggering a slurm job in the HPC has failed: {error}")
            self.__handle_message_failure(interruption=False)
            return

        # TODO: The worker blocks here till the slurm job finishes
        # TODO: Continuously check slurm job status here

        if slurm_job_return_code != 0:
            self.log.error(f"The slurm job failed for job_id: {self.current_message_job_id}")
            self.__handle_message_failure(interruption=False)
            return

        self.log.debug(f"The Nextflow process has finished successfully")
        job_state = "SUCCESS"
        self.log.info(f"Setting new state[{job_state}] of job_id: {self.current_message_job_id}")
        db.sync_set_workflow_job_state(self.current_message_job_id, job_state=job_state)
        self.has_consumed_message = False
        self.log.debug(f"Acking delivery tag: {self.current_message_delivery_tag}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __handle_message_failure(self, interruption: bool = False):
        job_state = "STOPPED"
        self.log.info(f"Setting new state[{job_state}] of job_id: {self.current_message_job_id}")
        db.sync_set_workflow_job_state(
            job_id=self.current_message_job_id,
            job_state=job_state
        )
        self.has_consumed_message = False

        if interruption:
            # self.log.debug(f"Nacking delivery tag: {self.current_message_delivery_tag}")
            # self.rmq_consumer._channel.basic_nack(delivery_tag=self.current_message_delivery_tag)
            # TODO: Sending ACK for now because it is hard to clean up without a mets workspace backup mechanism
            self.log.debug(f"Interruption Acking delivery tag: {self.current_message_delivery_tag}")
            self.rmq_consumer._channel.basic_ack(delivery_tag=self.current_message_delivery_tag)
            return

        self.log.debug(f"Acking delivery tag: {self.current_message_delivery_tag}")
        self.rmq_consumer._channel.basic_ack(delivery_tag=self.current_message_delivery_tag)

        # Reset the current message related parameters
        self.current_message_delivery_tag = None
        self.current_message_ws_id = None
        self.current_message_wf_id = None
        self.current_message_job_id = None

    # TODO: Ideally this method should be wrapped to be able
    #  to pass internal data from the Worker class required for the cleaning
    # The arguments to this method are passed by the caller from the OS
    def signal_handler(self, sig, frame):
        signal_name = signal.Signals(sig).name
        self.log.info(f"{signal_name} received from parent process[{getppid()}].")
        if self.has_consumed_message:
            self.log.info(f"Handling the message failure due to interruption: {signal_name}")
            self.__handle_message_failure(interruption=True)
        # TODO: Disconnect the RMQConsumer properly
        # TODO: Clean the remaining leftovers (if any)
        self.log.info("Exiting gracefully.")
        exit(0)

    # TODO: This should be further refined, currently it's just everything in one place
    def trigger_slurm_job(self, workspace_dir, job_dir, job_id, input_file_grp):
        batch_script_id = "submit_workflow_job.sh"
        nextflow_script_id = "template_workflow.nf"

        src_batch_script_path = f"{dirname(__file__)}/batch_scripts/{batch_script_id}"
        dst_batch_script_path = f"{self.hpc_connector.hpc_home_path}/batch_scripts/{batch_script_id}"
        self.hpc_connector.put_file(source=src_batch_script_path, destination=dst_batch_script_path)

        src_nextflow_script_path = f"{dirname(__file__)}/nextflow_workflows/{nextflow_script_id}"
        makedirs(f"/tmp/{job_id}")
        # Symlink the nextflow script
        os.symlink(
            src=src_nextflow_script_path,
            dst=f"/tmp/{job_id}/{nextflow_script_id}"
        )
        # Symlink the ocrd workspace
        os.symlink(
            src=workspace_dir,
            dst=f"/tmp/{job_id}/data"
        )

        src_slurm_workspace = f"/tmp/{job_id}"
        dst_slurm_workspace = f"{self.hpc_connector.hpc_home_path}/workflow_jobs/{job_id}/"
        self.hpc_connector.put_directory(
            source=src_slurm_workspace,
            destination=dst_slurm_workspace,
            recursive=True
        )

        # NOTE: The paths below must be a valid existing path inside the HPC
        # submit_slurm_workspace() method
        batch_script_path = f"{self.hpc_connector.hpc_home_path}/batch_scripts/{batch_script_id}"

        ssh_command = "bash -lc"
        ssh_command += " 'sbatch"
        ssh_command += f" {batch_script_path}"
        ssh_command += f" {job_id}"
        ssh_command += f" {nextflow_script_id}"
        ssh_command += f" {input_file_grp}'"

        # TODO: Non-blocking process in the background must be started instead
        # TODO: The results of the output, err, and return_code must be written to a file
        output, err, return_code = self.hpc_connector.execute_blocking(ssh_command)
        slurm_job_id = output.split(' ')[-1]

        self.log.info(f"Sbatch stdout: {output}")
        self.log.info(f"Sbatch job id: {slurm_job_id}")
        self.log.info(f"Sbatch stderr: {err}")
        self.log.info(f"Sbatch return code: {return_code}")

        sacct_command = "bash -lc"
        sacct_command += f" 'sacct -j {slurm_job_id} --format=jobid,state,exitcode'"

        while True:
            sleep(5)
            sacct_output, sacct_err, sacct_return_code = self.hpc_connector.execute_blocking(sacct_command)

            slurm_job_state = sacct_output.split('\n')[-1].split()[1]
            self.log.info(f"Sacct job state: {slurm_job_state}")
            if not slurm_job_state:
                continue

            slurm_waiting_states = ["PENDING", "RUNNING", "REQUEUED", "RESIZING"]
            if slurm_job_state not in slurm_waiting_states:
                break

        # Get the result dir from the HPC home folder
        self.hpc_connector.get_directory(source=dst_slurm_workspace, destination=job_dir, recursive=True)

        # Delete the result dir from the HPC home folder
        self.hpc_connector.execute_blocking(f"bash -lc 'rm -rf {dst_slurm_workspace}'")
        return return_code
