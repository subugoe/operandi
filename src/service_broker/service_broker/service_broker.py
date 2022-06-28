import os.path
import shutil
import requests
from clint.textui import progress
import time

from priority_queue.consumer import Consumer
from .ssh_communication import SSHCommunication

from .constants import (
    SERVICE_BROKER_HOST as HOST,
    SERVICE_BROKER_PORT as PORT,
)


# TODO: Implement the entire service broker properly
# Currently the functions are not modularized well enough


class ServiceBroker:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self._module_path = os.path.dirname(__file__)

        print(f"Service broker host:{host} port:{port}")
        self.consumer = Consumer()
        print("Consumer initiated")
        self.ssh = SSHCommunication()
        print("SSH connection successful")

    @staticmethod
    def download_mets_file(path_to_download, mets_url):
        filename = f"{path_to_download}/mets.xml"

        try:
            response = requests.get(mets_url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as file:
                    # Unfortunately the responses from GDZ does not contain
                    # content-length information in the response header
                    # The line below is a "bad" hack to find the size of the mets file
                    length = response.content.__sizeof__() - 33
                    size = (length / 512) + 1
                    for chunk in progress.bar(response.iter_content(chunk_size=512), expected_size=size):
                        if chunk:
                            file.write(chunk)
                            file.flush()
                return True

        except requests.exceptions.RequestException as e:
            print(f"f:download_mets_file, Exception: {e}")
            return False

    ###########################################################
    # Packs together the following:
    # a batch script,
    # a nextflow configuration,
    # a nextflow script
    # an ocrd-workspace/a mets file

    # Tree structure of the nextflow workspace:
    # nextflow_workspaces(dir):
    #   - nextflow_workspace_name(dir)
    #       - base_script.sh
    #       - bin(dir)
    #           - nextflow.config
    #           - seq_ocrd_wf_single_processor.nf (nextflow script)
    #           - ocrd-workspace(dir)
    #               - mets.xml
    ###########################################################
    # TODO: provide a better way for configuring paths
    def prepare_workspace(self, mets_url, workspace_name):
        base_script_path = f"{self._module_path}/batch_scripts/base_script.sh"
        nextflow_config_path = f"{self._module_path}/nextflow/configs/nextflow.config"
        nextflow_script_path = f"{self._module_path}/nextflow/scripts/seq_ocrd_wf_single_processor.nf"

        nextflow_workspaces_path = f"{self._module_path}/nextflow_workspaces"
        current_workspace_path = f"{nextflow_workspaces_path}/{workspace_name}"
        bin_path = f"{current_workspace_path}/bin"
        ocrd_workspace_path = f"{bin_path}/ocrd-workspace"

        if not os.path.exists(bin_path):
            # Under normal circumstances workspace names should not be duplicated
            # If that is the case, this call should raise an exception
            # For testing purposes currently exists_ok is set to True
            # to avoid the exception
            os.makedirs(bin_path, exist_ok=True)

        if os.path.exists(base_script_path):
            shutil.copy2(base_script_path, current_workspace_path)

        if os.path.exists(nextflow_config_path):
            shutil.copy2(nextflow_config_path, bin_path)

        if os.path.exists(nextflow_script_path):
            shutil.copy2(nextflow_script_path, bin_path)

        if not os.path.exists(ocrd_workspace_path):
            os.makedirs(ocrd_workspace_path)
            self.download_mets_file(ocrd_workspace_path, mets_url)

    def submit_files_of_workspace(self, workspace_name):
        source_path = f"{self._module_path}/nextflow_workspaces/{workspace_name}"
        self.ssh.put_directory(source=source_path,
                               destination=self.ssh.home_path,
                               recursive=True)

    def trigger_execution_for_workspace(self, workspace_name):
        # This is the batch script submitted to the SLURM scheduler in HPC
        base_script_path = f"{self.ssh.home_path}/{workspace_name}/base_script.sh"

        # Bash reads shell setup files, such as /etc/profile and bashrc, only if you log in interactively.
        # That's where the setup of the paths and modules happen.
        # You can bypass that by forcing bash to start a login shell:
        # $ ssh gwdu101.gwdg.de  "bash -lc 'srun --version'"

        ssh_command = f"bash -lc 'sbatch {base_script_path} {workspace_name}'"

        # The line below triggers the execution of the base_script.sh inside th
        output, err, return_code = self.ssh.execute_blocking(ssh_command)
        print(f"RC:{return_code}, ERR:{err}, O:{output}")

    def start_consuming(self, limit):
        consumed_counter = 0

        print(f"INFO: Waiting for messages. To exit press CTRL+C.")
        # Loops till there is a single message inside the queue
        while True:
            received_bytes = self.consumer.single_consume()
            if received_bytes is not None:
                received_string = received_bytes.decode('utf8')
                mets_url, mets_id = received_string.split(',')
                print(f"URL:{mets_url}")
                print(f"Workspace Name: {mets_id}")
                consumed_counter += 1
                self.prepare_workspace(mets_url=mets_url, workspace_name=mets_id)
                # print(f"Submitting files and triggering cluster execution is commented out!")
                self.submit_files_of_workspace(workspace_name=mets_id)
                self.trigger_execution_for_workspace(workspace_name=mets_id)

            # Consume only till the limit is reached
            if consumed_counter == limit:
                break

            time.sleep(2)

    # Callback method for the service broker
    def callback(ch, method, properties, body):
        # print(f"INFO: ch: {ch}")
        # print(f"INFO: method: {method}")
        # print(f"INFO: properties: {properties}")
        print(f"INFO: A METS URI has been consumed: {body}")

    def start_consuming_callback(self):
        # To consume continuously
        self.consumer.set_callback(self.callback)
        self.consumer.start_consuming()
