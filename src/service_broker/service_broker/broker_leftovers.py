import logging
import os.path
import shutil

from .constants import LOG_FORMAT, LOG_LEVEL
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
from .utils import download_mets_file


# TODO: These are leftovers from the Service Broker and
#  FileManager to be adopted by the separate Worker classes
class BrokerLeftovers:
    def __init__(self, hpc_host, hpc_username, hpc_key_path, local_execution):
        self.log = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
        logging.getLogger(__name__).setLevel(LOG_LEVEL)

        # Installation path of the module
        self._module_path = os.path.dirname(__file__)
        self._local_execution = local_execution

        if self._local_execution:
            self.ssh = None
            self.log.info("SSH disabled. Nothing will be submitted to the HPC.")
            self.log.info("The mockup version of the Service broker will be used.")
        else:
            self.ssh = SSHCommunication()
            self.ssh.connect_to_hpc(hpc_host, hpc_username, hpc_key_path)
            self.log.info("SSH connection successful.")

    def execute_on_local(self, mets_url, workspace_id):
        self.prepare_local_workspace(mets_url, workspace_id)
        return_code = self.trigger_local_nf_execution(workspace_id)
        # Local execution started successfully
        if return_code == 0:
            self.log.info(f"Execution started locally for workspace: {workspace_id}")
        else:
            self.log.error(f"Failed to start local run for workspace: {workspace_id}")

    def execute_on_hpc(self, mets_url, workspace_id):
        self.prepare_hpc_workspace(mets_url, workspace_id)
        self.submit_hpc_workspace(workspace_id)
        return_code, err, output = self.trigger_hpc_nf_execution(workspace_id)
        self.log.debug(f"RC:{return_code}, ERR:{err}, O:{output}")
        # Job submitted successfully
        if return_code == 0:
            self.log.info(f"Execution started on HPC for workspace: {workspace_id}")
        else:
            self.log.error(f"Failed to start on HPC run for workspace: {workspace_id}")

    def prepare_local_workspace(self, mets_url, workspace_id):
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

    def prepare_hpc_workspace(self, mets_url, workspace_id):
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

    def submit_hpc_workspace(self, workspace_id, remove_local=True):
        nf_workspace_dir = get_nf_workspace_dir(workspace_id, local=False)
        self.ssh.put_directory(source=nf_workspace_dir,
                               destination=self.ssh.hpc_home_path,
                               recursive=True)

        # Remove the workspace from the local storage after submitting to the HPC
        if remove_local:
            shutil.rmtree(nf_workspace_dir)

    @staticmethod
    def trigger_local_nf_execution(workspace_id):
        nf_script_path = get_nf_script(workspace_id, local=True)
        nf_workspace_dir = get_nf_workspace_dir(workspace_id, local=True)
        ocrd_workspace_dir = get_ocrd_workspace_dir(workspace_id, local=True)

        nf_process = trigger_nf_process(
            nf_workspace_dir=nf_workspace_dir,
            nf_script_path=nf_script_path,
            ocrd_workspace_dir=ocrd_workspace_dir
        )

        return nf_process

    def trigger_hpc_nf_execution(self, workspace_id):
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
