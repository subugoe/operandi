import os.path
import shutil
import requests
import subprocess
import shlex
from clint.textui import progress
from .ssh_communication import SSHCommunication
from priority_queue.consumer import Consumer
from priority_queue.constants import (
    RABBIT_MQ_HOST,
    RABBIT_MQ_PORT
)
from .constants import (
    HPC_HOST,
    HPC_USERNAME,
    HPC_KEY_PATH
)

# TODO: Implement the entire service broker properly
# Currently the functions are not modularized well enough


class ServiceBroker:
    def __init__(self,
                 rabbit_mq_host=RABBIT_MQ_HOST,
                 rabbit_mq_port=RABBIT_MQ_PORT,
                 hpc_host=HPC_HOST,
                 hpc_username=HPC_USERNAME,
                 hpc_key_path=HPC_KEY_PATH,
                 use_broker_mockup=False):
        self._module_path = os.path.dirname(__file__)
        self._home_dir_path = os.path.expanduser("~")
        self._use_broker_mockup = use_broker_mockup

        self.consumer = Consumer(
            username="operandi-broker",
            password="operandi-broker",
            rabbit_mq_host=rabbit_mq_host,
            rabbit_mq_port=rabbit_mq_port
        )
        print("Consumer initiated")

        # TODO: FIX THIS
        # Currently, the service broker cannot connect to the HPC environment
        # using SSH since there is no key pair inside the docker container

        # When running inside the container,
        # disable the self.ssh related commands manually!

        if self._use_broker_mockup:
            self.ssh = None
            print("SSH disabled. Nothing will be submitted to the HPC.")
            print("The mockup version of the Service broker will be used.")
        else:
            self.ssh = SSHCommunication(hpc_host=hpc_host,
                                        hpc_username=hpc_username,
                                        hpc_key_path=hpc_key_path,)
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
    def prepare_hpc_workspace(self, mets_url, workspace_name):
        base_script_path = f"{self._module_path}/batch_scripts/base_script.sh"
        nextflow_config_path = f"{self._module_path}/nextflow/configs/nextflow.config"
        nextflow_script_path = f"{self._module_path}/nextflow/scripts/hpc_seq_ocrd_wf_single_processor.nf"

        nextflow_workspaces_path = f"{self._home_dir_path}/OPERANDI_DATA/ws_hpc"
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

    ###########################################################
    # Packs together the following:
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
    def prepare_local_workspace(self, mets_url, workspace_name):
        nextflow_script_path = f"{self._module_path}/nextflow/scripts/local_seq_ocrd_wf_single_processor.nf"
        nextflow_workspaces_path = f"{self._home_dir_path}/OPERANDI_DATA/ws_local"
        current_workspace_path = f"{nextflow_workspaces_path}/{workspace_name}"
        bin_path = f"{current_workspace_path}/bin"
        ocrd_workspace_path = f"{bin_path}/ocrd-workspace"

        if not os.path.exists(bin_path):
            # Under normal circumstances workspace names should not be duplicated
            # If that is the case, this call should raise an exception
            # For testing purposes currently exists_ok is set to True
            # to avoid the exception
            os.makedirs(bin_path, exist_ok=True)

        if os.path.exists(nextflow_script_path):
            shutil.copy2(nextflow_script_path, bin_path)

        if not os.path.exists(ocrd_workspace_path):
            os.makedirs(ocrd_workspace_path)

        self.download_mets_file(ocrd_workspace_path, mets_url)

    def submit_files_of_workspace(self, workspace_name, remove_local=True):
        source_path = f"{self._home_dir_path}/OPERANDI_DATA/ws_hpc/{workspace_name}"
        self.ssh.put_directory(source=source_path,
                               destination=self.ssh.home_path,
                               recursive=True)

        # Remove the workspace from the local
        # after submitting to the HPC
        if remove_local:
            shutil.rmtree(source_path)

    def trigger_local_execution(self, workspace_name):
        source_path = f"{self._home_dir_path}/OPERANDI_DATA/ws_local/{workspace_name}"
        nextflow_script_path = f"{source_path}/bin/local_seq_ocrd_wf_single_processor.nf"
        workspace_path = f"{source_path}/bin/ocrd-workspace"
        nextflow_command = f"nextflow -bg run {nextflow_script_path} --volumedir {workspace_path} -with-report"
        out_path = open(f"{source_path}/output.txt", 'w')
        output = subprocess.call(shlex.split(nextflow_command),
                                 cwd=source_path,
                                 stdout=out_path)
        out_path.close()
        return output

    def trigger_hpc_execution(self, workspace_name):
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
        return return_code, err, output

    def start(self):
        self.consumer.define_consuming_listener(
            callback=self.mets_url_callback
        )

    def mets_url_callback(self, ch, method, properties, body):
        # print(f"{self}")
        # print(f"INFO: ch: {ch}")
        # print(f"INFO: method: {method}")
        # print(f"INFO: properties: {properties}")
        print(f"INFO: A METS URI has been consumed: {body}")

        if body:
            mets_url, mets_id = body.decode('utf8').split(',')
            if self._use_broker_mockup:
                self.consumer.reply_job_id(cluster_job_id="Running locally, no ID")
                self.prepare_local_workspace(mets_url=mets_url, workspace_name=mets_id)
                output = self.trigger_local_execution(workspace_name=mets_id)
                if output == 0:
                    print(f"{mets_id}, local execution of Nextflow has started.")
                else:
                    print(f"{mets_id}, there were problems with the local execution.")
            else:
                self.prepare_hpc_workspace(mets_url=mets_url, workspace_name=mets_id)
                self.submit_files_of_workspace(workspace_name=mets_id)
                return_code, err, output = self.trigger_hpc_execution(workspace_name=mets_id)

                # Job submitted successfully
                if return_code == 0:
                    # Example output message:
                    # "Submitted batch job XXXXXXXX"

                    # This is a temporal solution
                    # should be parsed more elegantly
                    job_id = output.split(" ")[3]
                    self.consumer.reply_job_id(cluster_job_id=job_id)
                else:
                    # No job ID assigned, failed
                    self.consumer.reply_job_id(cluster_job_id="No assigned ID")
