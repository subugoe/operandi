from logging import getLogger
from os.path import join
from requests import get as requests_get, post as requests_post
from requests.auth import HTTPBasicAuth
from time import sleep

from operandi_utils import get_log_file_path_prefix, is_url_responsive, reconfigure_all_loggers, receive_file
from operandi_utils.constants import LOG_LEVEL_CLIENT, StateJob

from .client_utils import check_server_responsiveness
from .constants import TRIES_TILL_TIMEOUT, USE_WORKSPACE_FILE_GROUP, WAIT_TIME_BETWEEN_POLLS


class OperandiClient:
    def __init__(self, server_address: str, auth: HTTPBasicAuth, log_level: int = LOG_LEVEL_CLIENT):
        self.auth = auth
        self.logger = getLogger("operandi_client.client")
        self.logger.setLevel(log_level)
        log_file_path = f"{get_log_file_path_prefix(module_type='client')}.log"
        # Reconfigure all loggers to the same format
        reconfigure_all_loggers(log_level=LOG_LEVEL_CLIENT, log_file_path=log_file_path)

        self.server_address = server_address
        check_server_responsiveness(self.logger, self.server_address)

    def _parse_response_field(self, response, field_key: str) -> str:
        response_json = response.json()
        self.logger.debug(response_json)
        resource_id = response_json.get(field_key, None)
        return resource_id

    def post_workspace_url(self, mets_url: str, file_grp: str = USE_WORKSPACE_FILE_GROUP) -> str:
        if not is_url_responsive(mets_url):
            msg = f"Workspace mets url is not responsive: {mets_url}"
            self.logger.error(msg)
            raise ValueError(msg)
        self.logger.info(f"Posting workspace mets url: {mets_url}")
        req_url_base = f"{self.server_address}/import_external_workspace"
        req_url_params = f"?mets_url={mets_url}&preserve_file_grps={file_grp}"
        req_url = f"{req_url_base}{req_url_params}"
        response = requests_post(url=req_url, auth=self.auth)
        workspace_id = self._parse_response_field(response=response, field_key="resource_id")
        if not workspace_id:
            raise ValueError(f"Failed to parse workspace id from response")
        self.logger.info(f"Response workspace id: {workspace_id}")
        return workspace_id

    def post_workspace_zip(self, ocrd_zip_path: str):
        self.logger.info(f"Uploading workspace ocrd zip: {ocrd_zip_path}")
        req_url_base = f"{self.server_address}/workspace"
        files = {"workspace": open(f"{ocrd_zip_path}", "rb")}
        response = requests_post(url=req_url_base, files=files, auth=self.auth)
        workspace_id = self._parse_response_field(response=response, field_key="resource_id")
        if not workspace_id:
            raise ValueError(f"Failed to parse workspace id from response")
        self.logger.info(f"Response workspace id: {workspace_id}")
        return workspace_id

    def post_workflow_nf_script(self, nf_script_path: str) -> str:
        self.logger.info(f"Uploading nextflow script file: {nf_script_path}")
        req_url_base = f"{self.server_address}/workflow"
        files = {"nextflow_script": open(f"{nf_script_path}", "rb")}
        response = requests_post(url=req_url_base, files=files, auth=self.auth)
        workflow_id = self._parse_response_field(response=response, field_key="resource_id")
        if not workflow_id:
            raise ValueError(f"Failed to parse workflow id from response")
        self.logger.info(f"Response workflow id: {workflow_id}")
        return workflow_id

    def post_workflow_job(
        self, workflow_id: str, workspace_id: str, input_file_grp: str = USE_WORKSPACE_FILE_GROUP,
        mets_base: str = "mets.xml", cpus: int = 8, ram: int = 32
    ) -> str:
        self.logger.info(f"Starting workflow job with workflow id: {workflow_id} on workspace id: {workspace_id}")
        workflow_args = {"workspace_id": workspace_id, "input_file_grp": input_file_grp, "mets_name": mets_base}
        sbatch_args = {"cpus": cpus, "ram": ram}
        request_json = {"workflow_id": workflow_id, "workflow_args": workflow_args, "sbatch_args": sbatch_args}
        self.logger.debug(request_json)
        req_url_base = f"{self.server_address}/workflow/{workflow_id}"
        response = requests_post(url=req_url_base, json=request_json, auth=self.auth)
        workflow_job_id = self._parse_response_field(response=response, field_key="resource_id")
        if not workflow_job_id:
            raise ValueError(f"Failed to parse workflow job id from response")
        self.logger.info(f"Response workflow job id: {workflow_job_id}")
        return workflow_job_id

    def get_workflow_job_state(self, workflow_id: str, job_id: str) -> str:
        self.logger.info(f"Checking state of workflow job id: {job_id}")
        req_url_base = f"{self.server_address}/workflow/{workflow_id}/{job_id}"
        response = requests_get(url=req_url_base, auth=self.auth)
        workflow_job_status = self._parse_response_field(response=response, field_key="job_state")
        if not workflow_job_status:
            raise ValueError(f"Failed to parse workflow job state from response")
        return workflow_job_status

    def poll_workflow_job_state(
        self, workflow_id: str, job_id: str, tries: int = TRIES_TILL_TIMEOUT, wait_time: int = WAIT_TIME_BETWEEN_POLLS
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
            if workflow_job_state == StateJob.SUCCESS:
                return True
            if workflow_job_state == StateJob.FAILED:
                return False
            tries_left -= 1
        return False

    def get_workspace_zip(self, workspace_id: str, download_dir: str) -> str:
        self.logger.info(f"Downloading workspace zip of: {workspace_id}")
        download_path = join(download_dir, f"{workspace_id}.ocrd.zip")
        req_url_base = f"{self.server_address}/workspace/{workspace_id}"
        # headers={"accept": "application/vnd.ocrd+zip"},
        response = requests_get(url=req_url_base, auth=self.auth)
        receive_file(response=response, download_path=download_path)
        self.logger.info(f"Downloaded workspace ocrd zip to: {download_path}")
        return download_path

    def get_workflow_job_zip(self, workflow_id: str, job_id: str, download_dir: str) -> str:
        self.logger.info(f"Downloading workflow job zip of: {job_id}")
        download_path = join(download_dir, f"{job_id}.zip")
        req_url_base = f"{self.server_address}/workflow/{workflow_id}/{job_id}/log"
        # headers={"accept": "application/vnd.zip"},
        response = requests_get(url=req_url_base, auth=self.auth)
        receive_file(response=response, download_path=download_path)
        self.logger.info(f"Downloaded workflow job zip to: {download_path}")
        return download_path
