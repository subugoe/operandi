import logging
import os.path
import shutil

from .constants import LOG_LEVEL
from .hpc_connector import (
    HPCConnector
)
from .utils import download_mets_file


# TODO: These are leftovers from the Service Broker and
#  FileManager to be adopted by the separate Worker classes
class BrokerLeftovers:
    def __init__(self, hpc_host, hpc_username, hpc_key_path, local_execution):
        self.log = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).setLevel(LOG_LEVEL)

        # Installation path of the module
        self._module_path = os.path.dirname(__file__)
        self._local_execution = local_execution

        if self._local_execution:
            self.hpc_connector = None
            self.log.info("HPC disabled. Nothing will be submitted to the HPC.")
            self.log.info("The mockup version of the Service broker will be used.")
        else:
            self.hpc_connector = HPCConnector()
            self.hpc_connector.connect_to_hpc(hpc_host, hpc_username, hpc_key_path)
            self.log.info("HPC connection successful.")


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
        self.hpc_connector.put_directory(source=nf_workspace_dir,
                                         destination=self.hpc_connector.hpc_home_path,
                                         recursive=True)

        # Remove the workspace from the local storage after submitting to the HPC
        if remove_local:
            shutil.rmtree(nf_workspace_dir)

    def trigger_hpc_nf_execution(self, workspace_id):
        script_id = "base_script.sh"
        batch_script_path = f"{self.hpc_connector.hpc_home_path}/{workspace_id}/{script_id}"

        ssh_command = "bash -lc"
        ssh_command += " 'sbatch"
        ssh_command += f" {batch_script_path}"
        ssh_command += f" {workspace_id}'"

        # TODO: Non-blocking process in the background must be started instead
        # TODO: The results of the output, err, and return_code must be written to a file
        output, err, return_code = self.hpc_connector.execute_blocking(ssh_command)
        return return_code, err, output
