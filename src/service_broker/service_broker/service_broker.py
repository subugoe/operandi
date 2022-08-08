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
    RABBIT_MQ_PORT,
)
from .constants import (
    HPC_HOST,
    HPC_USERNAME,
    HPC_KEY_PATH,
    OPERANDI_DATA_PATH,
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

        # Installation path of the module
        self._module_path = os.path.dirname(__file__)
        self._data_path = f'{os.path.expanduser("~")}/operandi-data'
        # self._data_path = OPERANDI_DATA_PATH
        self._use_broker_mockup = use_broker_mockup

        self.consumer = self.initiate_consumer(rabbit_mq_host, rabbit_mq_port)

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
            self.ssh = SSHCommunication()
            self.ssh.connect_to_hpc(hpc_host, hpc_username, hpc_key_path)
            print("SSH connection successful")

    @staticmethod
    def initiate_consumer(rabbit_mq_host, rabbit_mq_port):
        consumer = Consumer(
            username="operandi-broker",
            password="operandi-broker",
            rabbit_mq_host=rabbit_mq_host,
            rabbit_mq_port=rabbit_mq_port
        )
        print("Consumer initiated")
        return consumer

    def _copy_batch_script(self, workspace_id):
        script_id = "base_script.sh"
        src_path = f"{self._module_path}/batch_scripts/{script_id}"
        # destination is the workspace dir of workspace_id
        dst_path = self._get_nf_workspace_dir(workspace_id, local=False)

        if not os.path.exists(dst_path):
            os.makedirs(dst_path, exist_ok=True)

        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)

        print(f"Copied from: {src_path}, to: {dst_path}")

    def _copy_nextflow_config(self, workspace_id):
        config_id = "nextflow.config"
        src_path = f"{self._module_path}/nextflow/configs/{config_id}"
        workspace_dir = self._get_nf_workspace_dir(workspace_id, local=False)
        dst_path = f"{workspace_dir}/bin"

        if not os.path.exists(dst_path):
            os.makedirs(dst_path, exist_ok=True)

        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)

        print(f"Copied from: {src_path}, to: {dst_path}")

    def _copy_nextflow_script(self, workspace_id, local):
        if local:
            nf_script_id = "local_nextflow.nf"
            workspace_dir = self._get_nf_workspace_dir(workspace_id, local=True)
        else:
            nf_script_id = "hpc_nextflow.nf"
            workspace_dir = self._get_nf_workspace_dir(workspace_id, local=False)

        src_path = f"{self._module_path}/nextflow/scripts/{nf_script_id}"
        dst_path = f"{workspace_dir}/bin"

        if not os.path.exists(dst_path):
            os.makedirs(dst_path, exist_ok=True)

        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)

        print(f"Copied from: {src_path}, to: {dst_path}")

    def download_mets_file(self, mets_url, workspace_id, local):
        ocrd_workspace_dir = self._get_ocrd_workspace_dir(workspace_id, local=local)
        if not os.path.exists(ocrd_workspace_dir):
            os.makedirs(ocrd_workspace_dir)
        filename = f"{ocrd_workspace_dir}/mets.xml"

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
    #   - workspace_id(dir)
    #       - base_script.sh
    #       - bin(dir)
    #           - nextflow.config
    #           - hpc_nextflow.nf (nextflow script)
    #           - ocrd-workspace(dir)
    #               - mets.xml
    ###########################################################
    # TODO: provide a better way for configuring paths
    # TODO: Check if copying was successful.
    def prepare_hpc_workspace(self, mets_url, workspace_id):
        self._copy_batch_script(workspace_id)
        self._copy_nextflow_config(workspace_id)
        self._copy_nextflow_script(workspace_id, local=False)
        self.download_mets_file(mets_url, workspace_id, local=False)

    ###########################################################
    # Packs together the following:
    # a nextflow script
    # an ocrd-workspace/a mets file

    # Tree structure of the nextflow workspace:
    # nextflow_workspaces(dir):
    #   - workspace_id(dir)
    #       - bin(dir)
    #           - local_nextflow.nf (nextflow script)
    #           - ocrd-workspace(dir)
    #               - mets.xml
    ###########################################################
    # TODO: provide a better way for configuring paths
    # TODO: Check if copying was successful.
    def prepare_local_workspace(self, mets_url, workspace_id):
        self._copy_nextflow_script(workspace_id, local=True)
        self.download_mets_file(mets_url, workspace_id, local=True)

    def submit_files_of_workspace(self, workspace_id, remove_local=True):
        nf_workspace_dir = self._get_nf_workspace_dir(workspace_id, local=False)
        self.ssh.put_directory(source=nf_workspace_dir,
                               destination=self.ssh.hpc_home_path,
                               recursive=True)

        # Remove the workspace from the local
        # after submitting to the HPC
        if remove_local:
            shutil.rmtree(nf_workspace_dir)

    def _get_nf_workspace_dir(self, workspace_id, local):
        if local:
            # Set location to local - ws_local
            location = "ws_local"
        else:
            # Set location to hpc - ws_hpc
            location = "ws_hpc"
        nf_workspace_dir = f"{self._data_path}/{location}/{workspace_id}"
        print(f"Getting nf_workspace_dir: {nf_workspace_dir}")
        return nf_workspace_dir

    def _get_ocrd_workspace_dir(self, workspace_id, local):
        nf_workspace_dir = self._get_nf_workspace_dir(workspace_id, local)
        ocrd_workspace_dir = f"{nf_workspace_dir}/bin/ocrd-workspace"
        print(f"Getting ocrd_workspace_dir: {ocrd_workspace_dir}")
        return ocrd_workspace_dir

    def _get_nextflow_script(self, workspace_id, local):
        nf_workspace_dir = self._get_nf_workspace_dir(workspace_id, local)
        # This is the only supported Nextflow file currently
        if local:
            script_id = "local_nextflow.nf"
        else:
            script_id = "hpc_nextflow.nf"
        nf_script_path = f"{nf_workspace_dir}/bin/{script_id}"
        print(f"Getting nextflow_script: {nf_script_path}")
        return nf_script_path

    @staticmethod
    def _build_nf_command(nf_script_path, workspace_dir):
        nf_command = "nextflow -bg"
        nf_command += f" run {nf_script_path}"
        # When running an OCR-D docker container
        # It is enough to map the volume_dir.
        # Workspace path and mets path not needed
        nf_command += f" --volume_dir {workspace_dir}"
        # nf_command += f" --workspace {workspace_dir}/"
        # nf_command += f" --mets {workspace_dir}/mets.xml"
        nf_command += " -with-report"

        return nf_command

    @staticmethod
    def _get_nf_out_err_paths(workspace_id):
        nf_out = f'{workspace_id}/nextflow_out.txt'
        nf_err = f'{workspace_id}/nextflow_err.txt'

        return nf_out, nf_err

    def trigger_local_execution(self, workspace_id):
        nf_script_path = self._get_nextflow_script(workspace_id, local=True)
        nf_workspace_dir = self._get_nf_workspace_dir(workspace_id, local=True)
        ocrd_workspace_dir = self._get_ocrd_workspace_dir(workspace_id, local=True)

        print(f"nf_script_path: {nf_script_path}")
        print(f"nf_workspace_dir: {nf_workspace_dir}")
        print(f"ocrd_workspace_dir: {ocrd_workspace_dir}")

        nf_command = self._build_nf_command(nf_script_path, ocrd_workspace_dir)
        nf_out, nf_err = self._get_nf_out_err_paths(nf_workspace_dir)
        with open(nf_out, 'w+') as nf_out_file:
            with open(nf_err, 'w+') as nf_err_file:
                # Raises an exception if the subprocess fails
                # TODO: Catch and process exceptions properly
                # TODO: For some reason '.call' works '.run' does not. Investigate it ...
                nf_process = subprocess.call(shlex.split(nf_command),
                                             # shell=False,
                                             # check=True,
                                             cwd=nf_workspace_dir,
                                             stdout=nf_out_file,
                                             stderr=nf_err_file
                                             # universal_newlines=True
                                             )
        return nf_process

    @staticmethod
    def _build_sbatch_command(batch_script_path, workspace_dir):
        # Bash reads shell setup files only if you log in interactively.
        # You can bypass that by forcing bash to start a login shell.
        # E.g.: $ ssh gwdu101.gwdg.de  "bash -lc 'srun --version'"

        ssh_command = "bash -lc"
        ssh_command += " 'sbatch"
        ssh_command += f" {batch_script_path}"
        ssh_command += f" {workspace_dir}'"

        return ssh_command

    def _get_hpc_batch_script(self, workspace_id, script_id="base_script.sh"):
        # This is the batch script submitted to the SLURM scheduler in HPC
        script_path = f"{self.ssh.hpc_home_path}/{workspace_id}/{script_id}"
        return script_path

    def trigger_hpc_execution(self, workspace_id):
        batch_script_path = self._get_hpc_batch_script(workspace_id)
        ssh_command = self._build_sbatch_command(batch_script_path, workspace_id)
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
            mets_url, workspace_id = body.decode('utf8').split(',')
            if self._use_broker_mockup:
                self.prepare_local_workspace(mets_url, workspace_id)
                return_code = self.trigger_local_execution(workspace_id)
                if return_code == 0:
                    print(f"{workspace_id}, local execution of Nextflow has started.")
                else:
                    print(f"{workspace_id}, there were problems with the local execution.")
                self.consumer.reply_job_id(cluster_job_id="Running locally, no cluster job ID")
            else:
                self.prepare_hpc_workspace(mets_url, workspace_id)
                self.submit_files_of_workspace(workspace_id)
                return_code, err, output = self.trigger_hpc_execution(workspace_id)

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
