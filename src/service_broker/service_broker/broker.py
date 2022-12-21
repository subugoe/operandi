import os.path
import shutil
import requests
import subprocess
import shlex
from clint.textui import progress

from ocrd_webapi.rabbitmq import RMQConsumer
from rabbit_mq_utils.constants import (
    RABBIT_MQ_HOST as RMQ_HOST,
    RABBIT_MQ_PORT as RMQ_PORT,
    DEFAULT_EXCHANGER_NAME,
    DEFAULT_EXCHANGER_TYPE,
    DEFAULT_QUEUE_SERVER_TO_BROKER
)
from .constants import (
    HPC_HOST,
    HPC_USERNAME,
    HPC_KEY_PATH,
    WORKFLOWS_DIR,
    WORKSPACES_DIR
)
from .ssh_communication import SSHCommunication


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

        # Installation path of the module
        self._module_path = os.path.dirname(__file__)
        self._local_execution = local_execution
        self.__consumer = self.__initiate_consumer(rabbit_mq_host, rabbit_mq_port)

        # TODO: FIX THIS
        # Currently, the service broker cannot connect to the HPC environment
        # using SSH since there is no key pair inside the docker container

        # When running inside the container,
        # disable the self.ssh related commands manually!
        if self._local_execution:
            self.ssh = None
            print("ServiceBroker>__init__.py(): SSH disabled. Nothing will be submitted to the HPC.")
            print("ServiceBroker>__init__.py(): The mockup version of the Service broker will be used.")
        else:
            self.ssh = SSHCommunication()
            self.ssh.connect_to_hpc(hpc_host, hpc_username, hpc_key_path)
            print("ServiceBroker>__init__.py(): SSH connection successful")

    @staticmethod
    def __initiate_consumer(rabbit_mq_host, rabbit_mq_port):
        consumer = RMQConsumer(
            host=rabbit_mq_host,
            port=rabbit_mq_port,
            vhost="/"
        )
        consumer.authenticate_and_connect(
            username="operandi-broker",
            password="operandi-broker"
        )
        print("ServiceBroker>__initiate_consumer(): Consumer initiated")
        return consumer

    def start(self):
        # Specify the callback method, i.e.,
        # what to happen every time something is consumed
        self.__consumer.configure_consuming(
            queue_name=DEFAULT_QUEUE_SERVER_TO_BROKER,
            callback_method=self.__mets_url_callback
        )
        # The main thread blocks here
        self.__consumer.start_consuming()

    # The callback method provided to the Consumer listener
    def __mets_url_callback(self, ch, method, properties, body):
        if body:
            print(f"INFO: Channel: {ch}")
            print(f"INFO: Method: {method}")
            print(f"INFO: Properties: {properties}")
            print(f"INFO: Body: {body}")
            mets_url, workspace_id = body.decode('utf8').split(',')
            print(f"INFO: Mets URL: {mets_url}")
            print(f"INFO: Workspace_ID: {workspace_id}")
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
            print(f"INFO: Execution started locally: {workspace_id}")
        else:
            print(f"ERROR: Failed local run: {workspace_id}")

    def __execute_on_hpc(self, mets_url, workspace_id):
        self.__prepare_hpc_workspace(mets_url, workspace_id)
        self.__submit_hpc_workspace(workspace_id)
        return_code, err, output = self.__trigger_hpc_nf_execution(workspace_id)
        # Job submitted successfully
        if return_code == 0:
            print(f"INFO: Execution started on HPC: {workspace_id}")
        else:
            print(f"ERROR: Failed HPC run: {workspace_id}")

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
        self.__copy_nextflow_script(workspace_id, local=True)
        self.__download_mets_file(mets_url, workspace_id, local=True)

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
        self.__copy_batch_script(workspace_id)
        self.__copy_nextflow_config(workspace_id)
        self.__copy_nextflow_script(workspace_id, local=False)
        self.__download_mets_file(mets_url, workspace_id, local=False)

    def __submit_hpc_workspace(self, workspace_id, remove_local=True):
        nf_workspace_dir = self.__get_nf_workspace_dir(workspace_id, local=False)
        self.ssh.put_directory(source=nf_workspace_dir,
                               destination=self.ssh.hpc_home_path,
                               recursive=True)

        # Remove the workspace from the local storage after submitting to the HPC
        if remove_local:
            shutil.rmtree(nf_workspace_dir)

    def __download_mets_file(self, mets_url, workspace_id, local):
        ocrd_workspace_dir = self.__get_ocrd_workspace_dir(workspace_id, local=local)
        if not os.path.exists(ocrd_workspace_dir):
            os.makedirs(ocrd_workspace_dir)
        filename = f"{ocrd_workspace_dir}/mets.xml"

        try:
            response = requests.get(mets_url, stream=True)
            if response.status_code == 200:
                with open(filename, 'wb') as file:
                    # Unfortunately the responses from GDZ does not
                    # contain content-length information in the response
                    # header. The line below is a "bad" hack to find the
                    # size of the mets file
                    length = response.content.__sizeof__() - 33
                    size = (length / 512) + 1
                    # TODO: The progress bar is not working as expected
                    # TODO: Consider to remove it completely
                    for chunk in progress.bar(response.iter_content(chunk_size=512), expected_size=size):
                        if chunk:
                            file.write(chunk)
                            file.flush()
                return True

        except requests.exceptions.RequestException as e:
            print(f"ServiceBroker>__download_mets_file(): Exception: {e}")
            return False

    def __trigger_local_nf_execution(self, workspace_id):
        nf_script_path = self.__get_nextflow_script(workspace_id, local=True)
        nf_workspace_dir = self.__get_nf_workspace_dir(workspace_id, local=True)
        ocrd_workspace_dir = self.__get_ocrd_workspace_dir(workspace_id, local=True)

        nf_command = self.__build_nf_command(nf_script_path, ocrd_workspace_dir)
        nf_out, nf_err = self.__get_nf_out_err_paths(nf_workspace_dir)

        # TODO: Not a big fan of the nested structure, fix this to open/close files separately
        # TODO: Exception handling related to fd should be then more clear
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

    def __trigger_hpc_nf_execution(self, workspace_id):
        batch_script_path = self.__get_hpc_batch_script(workspace_id)
        ssh_command = self.__build_sbatch_command(batch_script_path, workspace_id)
        # TODO: Non-blocking process in the background must be started instead
        # TODO: The results of the output, err, and return_code must be written to a file
        output, err, return_code = self.ssh.execute_blocking(ssh_command)
        print(f"ServiceBroker>__trigger_hpc_execution(): RC:{return_code}, ERR:{err}, O:{output}")
        return return_code, err, output

    @staticmethod
    def __build_nf_command(nf_script_path, workspace_dir):
        nf_command = "nextflow -bg"  # -bg - run in the background
        nf_command += f" run {nf_script_path}"
        # When running an OCR-D docker container
        # It is enough to map the volume_dir.
        # Workspace path and mets path not needed
        nf_command += f" --volume_dir {workspace_dir}"
        # nf_command += f" --workspace {workspace_dir}/"
        # nf_command += f" --mets {workspace_dir}/mets.xml"
        nf_command += " -with-report"  # produce report.html

        return nf_command

    @staticmethod
    def __get_nf_out_err_paths(workspace_dir):
        nf_out = f'{workspace_dir}/nextflow_out.txt'
        nf_err = f'{workspace_dir}/nextflow_err.txt'

        return nf_out, nf_err

    @staticmethod
    def __build_sbatch_command(batch_script_path, workspace_dir):
        # Bash reads shell setup files only if you log in interactively.
        # You can bypass that by forcing bash to start a login shell.
        # E.g.: $ ssh gwdu101.gwdg.de  "bash -lc 'srun --version'"

        ssh_command = "bash -lc"
        ssh_command += " 'sbatch"
        ssh_command += f" {batch_script_path}"
        ssh_command += f" {workspace_dir}'"

        return ssh_command

    def __get_hpc_batch_script(self, workspace_id, script_id="base_script.sh"):
        # This is the batch script submitted to the SLURM scheduler in HPC
        script_path = f"{self.ssh.hpc_home_path}/{workspace_id}/{script_id}"
        return script_path

    def __get_nf_workspace_dir(self, workspace_id, local):
        if local:
            # Set location to local - ws_local
            location = "ws_local"
        else:
            # Set location to hpc - ws_hpc
            location = "ws_hpc"
        nf_workspace_dir = f"{WORKSPACES_DIR}/{location}/{workspace_id}"
        # print(f"Getting nf_workspace_dir: {nf_workspace_dir}")
        return nf_workspace_dir

    def __get_ocrd_workspace_dir(self, workspace_id, local):
        nf_workspace_dir = self.__get_nf_workspace_dir(workspace_id, local)
        ocrd_workspace_dir = f"{nf_workspace_dir}/bin/ocrd-workspace"
        # print(f"Getting ocrd_workspace_dir: {ocrd_workspace_dir}")
        return ocrd_workspace_dir

    def __get_nextflow_script(self, workspace_id, local):
        nf_workspace_dir = self.__get_nf_workspace_dir(workspace_id, local)
        # This is the only supported Nextflow file currently
        if local:
            script_id = "local_nextflow.nf"
        else:
            script_id = "hpc_nextflow.nf"
        nf_script_path = f"{nf_workspace_dir}/bin/{script_id}"
        # print(f"Getting nextflow_script: {nf_script_path}")
        return nf_script_path

    def __copy_batch_script(self, workspace_id, script_id="base_script.sh"):
        src_path = f"{self._module_path}/batch_scripts/{script_id}"
        # destination is the workspace dir of workspace_id
        dst_path = self.__get_nf_workspace_dir(workspace_id, local=False)

        if not os.path.exists(dst_path):
            os.makedirs(dst_path, exist_ok=True)

        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)

        # print(f"Copied from: {src_path}, to: {dst_path}")

    def __copy_nextflow_config(self, workspace_id, config_id="nextflow.config"):
        src_path = f"{self._module_path}/nextflow/configs/{config_id}"
        workspace_dir = self.__get_nf_workspace_dir(workspace_id, local=False)
        dst_path = f"{workspace_dir}/bin"

        if not os.path.exists(dst_path):
            os.makedirs(dst_path, exist_ok=True)

        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)

        # print(f"Copied from: {src_path}, to: {dst_path}")

    def __copy_nextflow_script(self, workspace_id, local):
        if local:
            nf_script_id = "local_nextflow.nf"
            workspace_dir = self.__get_nf_workspace_dir(workspace_id, local=True)
        else:
            nf_script_id = "hpc_nextflow.nf"
            workspace_dir = self.__get_nf_workspace_dir(workspace_id, local=False)

        src_path = f"{self._module_path}/nextflow/scripts/{nf_script_id}"
        dst_path = f"{workspace_dir}/bin"

        if not os.path.exists(dst_path):
            os.makedirs(dst_path, exist_ok=True)

        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)

        # print(f"Copied from: {src_path}, to: {dst_path}")

    # TODO: Conceptual implementation, not tested in any way yet
    @staticmethod
    def __send_bag_to_olahd(path_to_bag) -> str:
        # Ola-HD dev instance,
        # available only when connected to GOENET
        url = 'http://141.5.99.53/api/bag'
        files = {'file': open(path_to_bag, 'rb')}
        params = {'isGt': False}
        # The credentials here are already publicly available inside the ola-hd repo
        # Ignore docker warnings about exposed credentials
        response = requests.post(url, files=files, data=params, auth=("admin", "JW24G.xR"))
        if response.status_code >= 400:
            response.raise_for_status()
        return response.json()['pid']
