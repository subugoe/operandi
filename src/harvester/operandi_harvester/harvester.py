from logging import getLogger
from os import environ, makedirs
from os.path import dirname, join
from requests import get as requests_get
from requests.auth import HTTPBasicAuth
from typing import Dict

from operandi_client import OperandiClient
from operandi_utils import get_log_file_path_prefix, reconfigure_all_loggers
from operandi_utils.constants import LOG_LEVEL_HARVESTER

from .harvester_utils import build_vd18_remote_url, check_vd18_file_existence, load_vd18_data, save_vd18_data
from .constants import USE_WORKSPACE_FILE_GROUP, VD18_IDS_FILE, WAIT_TIME_BETWEEN_SUBMITS


class Harvester:
    def __init__(
        self, server_address: str, auth_username: str = environ.get("OPERANDI_HARVESTER_DEFAULT_USERNAME", None),
        auth_password: str = environ.get("OPERANDI_HARVESTER_DEFAULT_PASSWORD", None)
    ):
        if not auth_username or not auth_password:
            raise ValueError("Environment variables not set: harvester credentials")
        self.logger = getLogger("operandi_harvester.harvester")
        self.logger.setLevel(LOG_LEVEL_HARVESTER)
        log_file_path = f"{get_log_file_path_prefix(module_type='harvester')}.log"
        # Reconfigure all loggers to the same format
        reconfigure_all_loggers(log_level=LOG_LEVEL_HARVESTER, log_file_path=log_file_path)
        check_vd18_file_existence(self.logger)
        self._configure_defaults()
        self.vd18_data: Dict = load_vd18_data(self.logger)
        self.server_address = server_address
        self.logger.info(f"Operandi server address: {self.server_address}")
        self.auth = HTTPBasicAuth(auth_username, auth_password)
        # self.operandi_client = OperandiClient(server_address=self.server_address, auth=self.auth)


    def _configure_defaults(self):
        self.results_download_dir: str = join(dirname(__file__), "results")
        makedirs(self.results_download_dir, exist_ok=True)
        self.logger.info(f"Zipped results will be downloaded to dir: {self.results_download_dir}")

        # That workflow id is provided by the Operandi Server
        self.default_workflow_id = "default_workflow_with_MS"
        self.logger.info(f"The default nextflow workflow id used: {self.default_workflow_id}")

        self.dummy_ws_zip: str = join(dirname(__file__), "assets", "small_ws.ocrd.zip")
        self.dummy_ws_input_file_grp = "DEFAULT"
        self.logger.info(f"The default workspace zip to be used: {self.dummy_ws_zip}")

    def convert_txt_to_json(self):
        with open(VD18_IDS_FILE, mode="r") as f:
            for line in f:
                if not line:
                    break
                vd18_ppn_id = line.strip()
                if not vd18_ppn_id:
                    self.logger.warning(f"Failed to get vd18_ppn_id from line: {line}")
                    continue
                remote_url = build_vd18_remote_url(self.logger, vd18_ppn_id)
                if vd18_ppn_id not in self.vd18_data:
                    self.vd18_data[vd18_ppn_id] = {}
                    self.vd18_data[vd18_ppn_id]["url"] = f"{remote_url}"
                    try:
                        response = requests_get(url=remote_url, allow_redirects=True)
                        self.vd18_data[vd18_ppn_id]["content-length"] = len(response.content)
                        save_vd18_data(self.logger, self.vd18_data)
                    except Exception as error:
                        self.logger.info(f"Failed to get response for: {remote_url}, error: {error}")
                else:
                    self.logger.warning(f"{vd18_ppn_id} is already in the dict!")

    def harvest_once_dummy(self):
        self.logger.info("Harvesting one dummy cycle to get OCR-D results")
        workspace_id = self.operandi_client.post_workspace_zip(ocrd_zip_path=self.dummy_ws_zip)
        job_id = self.operandi_client.post_workflow_job(
            workflow_id=self.default_workflow_id, workspace_id=workspace_id, input_file_grp=self.dummy_ws_input_file_grp)
        has_finished = self.operandi_client.poll_workflow_job_state(workflow_id=self.default_workflow_id, job_id=job_id)
        if not has_finished:
            raise ValueError("The workflow job state polling failed or reached a timeout")
        self.operandi_client.get_workspace_zip(workspace_id=workspace_id, download_dir=self.results_download_dir)
        self.operandi_client.get_workflow_job_zip(
            workflow_id=self.default_workflow_id, job_id=job_id, download_dir=self.results_download_dir)

    def start_harvesting(self, limit: int = 0):
        self.logger.info(f"Harvesting started with limit: {limit}")
        self.logger.info(f"Mets URL will be submitted every {WAIT_TIME_BETWEEN_SUBMITS} seconds.")
        harvested_counter = 0

        # Reads vd18 file line by line
        with open(VD18_IDS_FILE, mode="r") as f:
            for line in f:
                if not line:
                    break
                vd18_ppn_id = line.strip()
                if not vd18_ppn_id:
                    raise ValueError(f"Failed to get mets id from line: {line}")
                mets_remote_url = build_vd18_remote_url(self.logger, vd18_ppn_id)
                self.harvest_one_cycle(mets_url=mets_remote_url)
                harvested_counter += 1
                # If the limit is reached stop harvesting
                if harvested_counter == limit:
                    break

    def harvest_one_cycle(self, mets_url: str):
        workspace_id = self.operandi_client.post_workspace_url(mets_url=mets_url)
        job_id = self.operandi_client.post_workflow_job(
            workflow_id=self.default_workflow_id, workspace_id=workspace_id, input_file_grp=USE_WORKSPACE_FILE_GROUP)
        has_finished = self.operandi_client.poll_workflow_job_state(workflow_id=self.default_workflow_id, job_id=job_id)
        if not has_finished:
            raise ValueError("The workflow job state polling failed or reached a timeout")
