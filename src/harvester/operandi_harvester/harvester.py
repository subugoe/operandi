import logging
from os import environ
from os.path import dirname, exists, join, isfile
from requests import get, post
from requests.auth import HTTPBasicAuth
from time import sleep

from operandi_utils import get_log_file_path_prefix, is_url_responsive, reconfigure_all_loggers, receive_file
from operandi_utils.constants import LOG_LEVEL_HARVESTER
from .constants import (
    TRIES_TILL_TIMEOUT,
    USE_WORKSPACE_FILE_GROUP,
    VD18_IDS_FILE,
    VD18_METS_EXT,
    VD18_URL,
    WAIT_TIME_BETWEEN_SUBMITS,
    WAIT_TIME_BETWEEN_POLLS
)


class Harvester:
    def __init__(
            self,
            server_address: str,
            auth_username: str = environ.get("OPERANDI_HARVESTER_DEFAULT_USERNAME", None),
            auth_password: str = environ.get("OPERANDI_HARVESTER_DEFAULT_PASSWORD", None)
    ):
        self.logger = logging.getLogger("operandi_harvester.harvester")
        self.logger.setLevel(LOG_LEVEL_HARVESTER)

        log_file_path = f"{get_log_file_path_prefix(module_type='harvester')}.log"

        # Reconfigure all loggers to the same format
        reconfigure_all_loggers(
            log_level=LOG_LEVEL_HARVESTER,
            log_file_path=log_file_path
        )

        if not auth_username or not auth_password:
            raise ValueError("Environment variables not set: harvester credentials")
        if not exists(VD18_IDS_FILE):
            raise FileNotFoundError(f"Path does not exist: {VD18_IDS_FILE}")
        if not isfile(VD18_IDS_FILE):
            raise FileNotFoundError(f"Path is not a file: {VD18_IDS_FILE}")

        self.results_download_dir: str = join(dirname(__file__), "results")
        self.default_workflow_id = None
        self.default_nf_workflow: str = join(dirname(__file__), "assets", "default_workflow.nf")
        self.dummy_ws_zip: str = join(dirname(__file__), "assets", "dummy_ws.ocrd.zip")
        self.dummy_ws_input_file_grp = "OCR-D-IMG"

        self.logger.info(f"Operandi server address: {server_address}")
        self.logger.info(f"Zipped results will be downloaded to dir: {self.results_download_dir}")
        self.logger.info(f"The default nextflow workflow used: {self.default_nf_workflow}")

        # The address of the Operandi Server
        self.server_address = server_address
        if not is_url_responsive(server_address):
            raise ConnectionError(f"The Operandi Server is not responding: {server_address}")

        # The authentication used for interactions with the Operandi Server
        self.auth = HTTPBasicAuth(auth_username, auth_password)

    def harvest_once_dummy(self):
        self.logger.info("Harvesting one dummy cycle to get OCR-D results")
        workflow_id = self.post_workflow_nf_script(nf_script_path=self.default_nf_workflow)
        workspace_id = self.post_workspace_zip(ocrd_zip_path=self.dummy_ws_zip)
        job_id = self.post_workflow_job(
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            input_file_grp=self.dummy_ws_input_file_grp
        )
        has_finished = self.poll_workflow_job_state(workflow_id=workflow_id, job_id=job_id)
        if not has_finished:
            raise ValueError("The workflow job state polling failed or reached a timeout")
        self.get_workspace_zip(workspace_id=workspace_id, download_dir=self.results_download_dir)
        self.get_workflow_job_zip(workflow_id=workflow_id, job_id=job_id, download_dir=self.results_download_dir)

    def start_harvesting(self, limit: int = 0):
        self.logger.info(f"Harvesting started with limit: {limit}")
        self.logger.info(f"Mets URL will be submitted every {WAIT_TIME_BETWEEN_SUBMITS} seconds.")
        harvested_counter = 0

        # Reads vd18 file line by line
        with open(VD18_IDS_FILE, mode="r") as f:
            for line in f:
                if not line:
                    break
                mets_id = line.strip()
                if not mets_id:
                    raise ValueError(f"Failed to get mets id from line: {line}")
                mets_remote_url = f"{VD18_URL}{mets_id}{VD18_METS_EXT}"
                self.harvest_one_cycle(mets_url=mets_remote_url, nf_script_path=self.default_nf_workflow)
                harvested_counter += 1
                # If the limit is reached stop harvesting
                if harvested_counter == limit:
                    break

    def harvest_one_cycle(self, mets_url: str, nf_script_path: str, reuse_workflow: bool = True):
        # Whether to reuse workflow_id of previously uploaded workflow
        # script to avoid uploading the same script over and over again
        if reuse_workflow:
            if self.default_workflow_id:
                workflow_id = self.default_workflow_id
            else:
                workflow_id = self.post_workflow_nf_script(nf_script_path=nf_script_path)
                self.default_workflow_id = workflow_id
        else:
            workflow_id = self.post_workflow_nf_script(nf_script_path=nf_script_path)

        workspace_id = self.post_workspace_url(mets_url=mets_url)
        job_id = self.post_workflow_job(
            workflow_id=self.default_workflow_id,
            workspace_id=workspace_id,
            input_file_grp=USE_WORKSPACE_FILE_GROUP
        )
        has_finished = self.poll_workflow_job_state(workflow_id=workflow_id, job_id=job_id)
        if not has_finished:
            raise ValueError("The workflow job state polling failed or reached a timeout")

    def post_workspace_url(self, mets_url: str) -> str:
        if not is_url_responsive(mets_url):
            raise ValueError(f"Workspace mets url is not responsive: {mets_url}")
        self.logger.info(f"Posting workspace mets url: {mets_url}")
        response = post(
            url=f"{self.server_address}/workspace/import_external?mets_url={mets_url}",
            auth=self.auth
        )
        self.logger.debug(response.json())
        workspace_id = response.json().get('resource_id', None)
        if not workspace_id:
            raise ValueError(f"Failed to parse workspace id from response")
        self.logger.info(f"Response workspace id: {workspace_id}")
        return workspace_id

    def post_workspace_zip(self, ocrd_zip_path: str):
        self.logger.info(f"Posting workspace ocrd zip: {ocrd_zip_path}")
        response = post(
            url=f"{self.server_address}/workspace",
            files={"workspace": open(f"{ocrd_zip_path}", "rb")},
            auth=self.auth
        )
        self.logger.debug(response.json())
        workspace_id = response.json().get("resource_id", None)
        if not workspace_id:
            raise ValueError(f"Failed to parse workspace id from response")
        self.logger.info(f"Response workspace id: {workspace_id}")
        return workspace_id

    def post_workflow_nf_script(self, nf_script_path: str) -> str:
        self.logger.info(f"Posting nextflow script file: {nf_script_path}")
        response = post(
            url=f"{self.server_address}/workflow",
            files={"nextflow_script": open(f"{nf_script_path}", "rb")},
            auth=self.auth
        )
        self.logger.debug(response.json())
        workflow_id = response.json().get("resource_id", None)
        if not workflow_id:
            raise ValueError(f"Failed to parse workflow id from response")
        self.logger.info(f"Response workflow id: {workflow_id}")
        return workflow_id

    def post_workflow_job(
            self,
            workflow_id: str,
            workspace_id: str,
            input_file_grp: str = "DEFAULT",
            mets_base: str = "mets.xml",
            cpus: int = 4,
            ram: int = 32
    ) -> str:
        self.logger.info(f"Posting workflow job with workflow id: {workflow_id} on workspace id: {workspace_id}")
        request_json = {
            "workflow_id": workflow_id,
            "workflow_args": {
                "workspace_id": workspace_id,
                "input_file_grp": input_file_grp,
                "mets_name": mets_base
            },
            "sbatch_args": {
                "cpus": cpus,
                "ram": ram
            }
        }
        self.logger.debug(request_json)
        response = post(
            url=f"{self.server_address}/workflow/{workflow_id}",
            json=request_json,
            auth=self.auth
        )
        self.logger.debug(response.json())
        workflow_job_id = response.json().get("resource_id", None)
        if not workflow_job_id:
            raise ValueError(f"Failed to parse workflow job id from response")
        self.logger.info(f"Response workflow job id: {workflow_job_id}")
        return workflow_job_id

    def get_workflow_job_state(self, workflow_id: str, job_id: str) -> str:
        self.logger.info(f"Checking state of workflow job id: {job_id}")
        response = get(
            url=f"{self.server_address}/workflow/{workflow_id}/{job_id}",
            auth=self.auth
        )
        self.logger.debug(response.json())
        workflow_job_status = response.json().get("job_state", None)
        if not workflow_job_status:
            raise ValueError(f"Failed to parse workflow job state from response")
        return workflow_job_status

    def poll_workflow_job_state(
            self,
            workflow_id: str,
            job_id: str,
            tries: int = TRIES_TILL_TIMEOUT,
            wait_time: int = WAIT_TIME_BETWEEN_POLLS
    ) -> bool:
        self.logger.info(f"Starting polling the state of workflow job: {job_id}")
        self.logger.info(f"Amount of polls to be performed: {tries}, every {wait_time} secs.")
        tries_left = tries
        while tries_left > 0:
            self.logger.info(f"Checking the job state after {wait_time} seconds")
            sleep(wait_time)

            try:
                workflow_job_state = self.get_workflow_job_state(workflow_id=workflow_id, job_id=job_id)
            except Exception as error:
                self.logger.exception(f"Checking workflow job state has failed: {error}")
                return False

            self.logger.info(f"Response workflow job state: {workflow_job_state}")
            if workflow_job_state == "SUCCESS":
                return True
            if workflow_job_state == "FAILED":
                return False
            tries_left -= 1

    def get_workspace_zip(self, workspace_id: str, download_dir: str) -> str:
        self.logger.info(f"Getting workspace zip of: {workspace_id}")
        download_path = join(download_dir, f"{workspace_id}.ocrd.zip")
        response = get(
            url=f"{self.server_address}/workspace/{workspace_id}",
            headers={"accept": "application/vnd.ocrd+zip"},
            auth=self.auth
        )
        receive_file(response=response, download_path=download_path)
        self.logger.info(f"Downloaded workspace ocrd zip to: {download_path}")
        return download_path

    def get_workflow_job_zip(self, workflow_id: str, job_id: str, download_dir: str) -> str:
        self.logger.info(f"Getting workflow job zip of: {job_id}")
        download_path = join(download_dir, f"{job_id}.zip")
        response = get(
            url=f"{self.server_address}/workflow/{workflow_id}/{job_id}",
            headers={'accept': 'application/vnd.zip'},
            auth=self.auth
        )
        receive_file(response=response, download_path=download_path)
        self.logger.info(f"Downloaded workflow job zip to: {download_path}")
        return download_path
