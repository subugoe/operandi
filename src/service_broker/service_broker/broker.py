import os.path
import shutil

import logging

from ocrd_webapi.rabbitmq import RMQConsumer
from rabbit_mq_utils.constants import (
    RABBIT_MQ_HOST as RMQ_HOST,
    RABBIT_MQ_PORT as RMQ_PORT,
    DEFAULT_EXCHANGER_NAME,
    DEFAULT_EXCHANGER_TYPE,
    DEFAULT_QUEUE_SERVER_TO_BROKER,
    DEFAULT_QUEUE_HARVESTER_TO_BROKER
)
from .constants import (
    HPC_HOST,
    HPC_USERNAME,
    HPC_KEY_PATH,
    LOG_LEVEL,
    LOG_FORMAT,
)
from .file_manager import (
    copy_batch_script,
    copy_nextflow_config,
    copy_nextflow_script,
    get_nf_script,
    get_nf_workspace_dir,
    get_ocrd_workspace_dir,

)
from .nextflow import trigger_nf_process
from .ssh_communication import (
    build_sbatch_command,
    build_hpc_batch_script_path,
    SSHCommunication
)
from .utils import (
    download_mets_file,
    send_bag_to_ola_hd
)


# TODO: Implement the entire service broker properly
# Currently the functions are not modularized well enough


class ServiceBroker:
    def __init__(self,
                 rabbit_mq_host=RMQ_HOST,
                 rabbit_mq_port=RMQ_PORT,
                 hpc_host=HPC_HOST,
                 hpc_username=HPC_USERNAME,
                 hpc_key_path=HPC_KEY_PATH,
                 local_execution=False):

        logger = logging.getLogger(__name__)
        # Set the global logging level to INFO
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
        # Set the ServiceBroker logging level to LOG_LEVEL
        logging.getLogger(__name__).setLevel(LOG_LEVEL)
        self._logger = logger

        # Installation path of the module
        self._module_path = os.path.dirname(__file__)
        self._local_execution = local_execution
        self.__consumer_from_server_queue = self.__initiate_consumer(
            rabbit_mq_host,
            rabbit_mq_port,
            logger_name="operandi-broker_consumer_server-queue"
        )
        self.__consumer_from_harvester_queue = self.__initiate_consumer(
            rabbit_mq_host,
            rabbit_mq_port,
            logger_name="operandi-broker_consumer_harvester-queue"
        )

        # TODO: FIX THIS
        # Currently, the service broker cannot connect to the HPC environment
        # using SSH since there is no key pair inside the docker container

        # When running inside the container,
        # disable the self.ssh related commands manually!
        if self._local_execution:
            self.ssh = None
            self._logger.info("SSH disabled. Nothing will be submitted to the HPC.")
            self._logger.info("The mockup version of the Service broker will be used.")
        else:
            self.ssh = SSHCommunication()
            self.ssh.connect_to_hpc(hpc_host, hpc_username, hpc_key_path)
            self._logger.info("SSH connection successful.")

    @staticmethod
    def __initiate_consumer(rabbit_mq_host, rabbit_mq_port, logger_name):
        consumer = RMQConsumer(
            host=rabbit_mq_host,
            port=rabbit_mq_port,
            vhost="/",
            logger_name=logger_name
        )
        consumer.authenticate_and_connect(
            username="default-consumer",
            password="default-consumer"
        )
        return consumer

    def start_listening_to_server_queue(self):
        # Specify the callback method, i.e.,
        # what to happen every time something is consumed
        self.__consumer_from_server_queue.configure_consuming(
            queue_name=DEFAULT_QUEUE_SERVER_TO_BROKER,
            callback_method=self.__mets_url_callback
        )
        # The main thread blocks here
        self.__consumer_from_server_queue.start_consuming()

    def start_listening_to_harvester_queue(self):
        # Specify the callback method, i.e.,
        # what to happen every time something is consumed
        self.__consumer_from_harvester_queue.configure_consuming(
            queue_name=DEFAULT_QUEUE_HARVESTER_TO_BROKER,
            callback_method=self.__mets_url_callback
        )
        # The main thread blocks here
        self.__consumer_from_harvester_queue.start_consuming()

    # The callback method provided to the Consumer listener
    def __mets_url_callback(self, ch, method, properties, body):
        if body:
            self._logger.debug(f"ch: {ch}, method: {method}, properties: {properties}, body: {body}")
            mets_url, workspace_id = body.decode('utf8').split(',')
            self._logger.info(f"Received_URL: {mets_url} Received_WS_ID: {workspace_id}")
            if self._local_execution:
                self.__execute_on_local(mets_url, workspace_id)
            else:
                self.__execute_on_hpc(mets_url, workspace_id)

            # Send an acknowledgement back
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def __execute_on_local(self, mets_url, workspace_id):
        self.__prepare_local_workspace(mets_url, workspace_id)
        return_code = self.__trigger_local_nf_execution(workspace_id)
        # Local execution started successfully
        if return_code == 0:
            self._logger.info(f"Execution started locally for workspace: {workspace_id}")
        else:
            self._logger.error(f"Failed to start local run for workspace: {workspace_id}")

    def __execute_on_hpc(self, mets_url, workspace_id):
        self.__prepare_hpc_workspace(mets_url, workspace_id)
        self.__submit_hpc_workspace(workspace_id)
        return_code, err, output = self.__trigger_hpc_nf_execution(workspace_id)
        self._logger.debug(f"RC:{return_code}, ERR:{err}, O:{output}")
        # Job submitted successfully
        if return_code == 0:
            self._logger.info(f"Execution started on HPC for workspace: {workspace_id}")
        else:
            self._logger.error(f"Failed to start on HPC run for workspace: {workspace_id}")

    def __prepare_local_workspace(self, mets_url, workspace_id):
        ###########################################################
        # Tree structure of the nextflow local workspace:
        # ws_local (dir):
        #   - {workspace_id} (dir)
        #       - bin (dir)
        #           - local_nextflow.nf (nextflow script)
        #           - ocrd-workspace (dir)
        #               - mets.xml
        ###########################################################
        copy_nextflow_script(workspace_id, local=True)
        ocrd_workspace_dir = get_ocrd_workspace_dir(workspace_id, local=True)
        download_mets_file(mets_url, ocrd_workspace_dir)

    def __prepare_hpc_workspace(self, mets_url, workspace_id):
        ###########################################################
        # Tree structure of the nextflow hpc workspace:
        # ws_hpc (dir):
        #   - {workspace_id} (dir)
        #       - base_script.sh (batch script)
        #       - bin(dir)
        #           - nextflow.config
        #           - hpc_nextflow.nf (nextflow script)
        #           - ocrd-workspace (dir)
        #               - mets.xml
        ###########################################################
        copy_batch_script(workspace_id)
        copy_nextflow_config(workspace_id)
        copy_nextflow_script(workspace_id, local=False)
        ocrd_workspace_dir = get_ocrd_workspace_dir(workspace_id, local=False)
        download_mets_file(mets_url, ocrd_workspace_dir)

    def __submit_hpc_workspace(self, workspace_id, remove_local=True):
        nf_workspace_dir = get_nf_workspace_dir(workspace_id, local=False)
        self.ssh.put_directory(source=nf_workspace_dir,
                               destination=self.ssh.hpc_home_path,
                               recursive=True)

        # Remove the workspace from the local storage after submitting to the HPC
        if remove_local:
            shutil.rmtree(nf_workspace_dir)

    def __trigger_local_nf_execution(self, workspace_id):
        nf_script_path = get_nf_script(workspace_id, local=True)
        nf_workspace_dir = get_nf_workspace_dir(workspace_id, local=True)
        ocrd_workspace_dir = get_ocrd_workspace_dir(workspace_id, local=True)

        nf_process = trigger_nf_process(
            nf_workspace_dir=nf_workspace_dir,
            nf_script_path=nf_script_path,
            ocrd_workspace_dir=ocrd_workspace_dir
        )

        return nf_process

    def __trigger_hpc_nf_execution(self, workspace_id):
        batch_script_path = build_hpc_batch_script_path(
            self.ssh.hpc_home_path,
            workspace_id
        )
        ssh_command = build_sbatch_command(
            batch_script_path,
            workspace_id
        )
        # TODO: Non-blocking process in the background must be started instead
        # TODO: The results of the output, err, and return_code must be written to a file
        output, err, return_code = self.ssh.execute_blocking(ssh_command)
        return return_code, err, output
