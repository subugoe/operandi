import logging
from requests.auth import HTTPBasicAuth
from os.path import exists, isfile
import time
from typing import Union

from .constants import (
    VD18_IDS_FILE,
    VD18_METS_EXT,
    VD18_URL,
    WAIT_TIME_BETWEEN_SUBMITS,
    WAIT_TIME_BETWEEN_POLLS,
    LOG_LEVEL,
    LOG_FORMAT,
)

from .server_requests import (
    get_workflow_job_status,
    post_workflow_job,
    post_workflow_script,
    post_workspace_url,
    post_workspace
)

from operandi_utils import is_url_responsive


class Harvester:
    def __init__(self, server_address: str, auth_username: str, auth_password: str):
        self.logger = logging.getLogger(__name__)
        logging.getLogger(__name__).setLevel(LOG_LEVEL)
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

        # The address of the Operandi Server
        self.server_address = server_address
        # The authentication used for interactions with the Operandi Server
        self.auth = HTTPBasicAuth(auth_username, auth_password)

    def harvest_once_dummy(self):
        workflow_id = self._post_workflow(nf_script_name="default_workflow.nf")
        if not workflow_id:
            raise ValueError("Failed to upload workflow script")
        workspace_id = self._post_workspace(ocrd_zip_name="dummy_ws.ocrd.zip")
        if not workspace_id:
            raise ValueError("Failed to upload ocrd workspace zip")
        job_id = self._post_workflow_job(
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            input_file_grp="OCR-D-IMG"
        )
        if not job_id:
            raise ValueError("Failed to start workflow job")
        has_finished = self._poll_workflow_job_status(
            workflow_id=workflow_id,
            job_id=job_id
        )
        if not has_finished:
            raise ValueError("The workflow job polling failed or reached a timeout")

    def start_harvesting(self, limit=0):
        if not exists(VD18_IDS_FILE):
            self.logger.error(f"Path does not exist: {VD18_IDS_FILE}")
            exit(1)

        if not isfile(VD18_IDS_FILE):
            self.logger.error(f"Path is not a file: {VD18_IDS_FILE}")
            exit(1)

        self.logger.info(f"Harvesting started with limit:{limit}")
        self.logger.info(f"Mets URL will be submitted every {WAIT_TIME_BETWEEN_SUBMITS} seconds.")
        harvested_counter = 0

        # Reads vd18 file line by line
        with open(VD18_IDS_FILE, mode="r") as f:
            for line in f:
                if not line:
                    break
                mets_id = line.strip()
                self._harvest_one_cycle(mets_id)
                harvested_counter += 1
                # If the limit is reached stop harvesting
                if harvested_counter == limit:
                    break

    def _harvest_one_cycle(self, mets_id):
        if not mets_id:
            self.logger.error(f"The mets_id is None")
            return False
        mets_url = f"{VD18_URL}{mets_id}{VD18_METS_EXT}"
        workflow_id = self._post_workflow(nf_script_name="nextflow_script.nf")
        if not workflow_id:
            raise ValueError("Failed to upload workflow script")
        workspace_id = self._post_workspace_url(mets_url=mets_url)
        if not workspace_id:
            raise ValueError("Failed to upload ocrd workspace zip")
        job_id = self._post_workflow_job(
            workflow_id=workflow_id,
            workspace_id=workspace_id,
            input_file_grp="DEFAULT"
        )
        if not job_id:
            raise ValueError("Failed to start workflow job")
        has_finished = self._poll_workflow_job_status(
            workflow_id=workflow_id,
            job_id=job_id
        )
        if not has_finished:
            raise ValueError("The workflow job polling failed or reached a timeout")

    def _post_workspace(self, ocrd_zip_name: str):
        try:
            self.logger.info(f"Post workspace ocrd zip: {ocrd_zip_name}")
            workspace_id = post_workspace(
                server_address=self.server_address,
                auth=self.auth,
                ocrd_zip_name=ocrd_zip_name
            )
            self.logger.info(f"Response workspace id: {workspace_id}")
        except Exception as e:
            self.logger.error(f"Posting workspace ocrd zip failed: {e}")
            return None
        return workspace_id

    def _post_workspace_url(self, mets_url: str) -> Union[str, None]:
        # Check if the VD18 repository responds to the url
        if not is_url_responsive(mets_url):
            self.logger.error(f"Workspace mets url is not responsive: {mets_url}")
            return None

        # Post Workspace URL to get workspace_id
        try:
            self.logger.info(f"Posting workspace mets url: {mets_url}")
            workspace_id = post_workspace_url(
                server_address=self.server_address,
                auth=self.auth,
                mets_url=mets_url
            )
            self.logger.info(f"Response workspace id: {workspace_id}")
        except Exception as e:
            self.logger.error(f"Posting workspace mets url failed: {e}")
            return None
        return workspace_id

    def _post_workflow(self, nf_script_name: str) -> Union[str, None]:
        try:
            self.logger.info(f"Post nextflow script: {nf_script_name}")
            workflow_id = post_workflow_script(
                server_address=self.server_address,
                auth=self.auth,
                nf_script_name=nf_script_name
            )
            self.logger.info(f"Response workflow id: {workflow_id}")
        except Exception as e:
            self.logger.error(f"Posting nextflow script failed: {e}")
            return None
        return workflow_id

    def _post_workflow_job(self, workflow_id: str, workspace_id: str, input_file_grp: str) -> Union[str, None]:
        # Post Workflow Job with workflow_id and workspace_id obtained previously
        try:
            self.logger.info(
                f"Posting workflow job, "
                f"wf_id: {workflow_id}, "
                f"ws_id: {workspace_id}"
            )
            workflow_job_id = post_workflow_job(
                server_address=self.server_address,
                auth=self.auth,
                workflow_id=workflow_id,
                workspace_id=workspace_id,
                input_file_grp=input_file_grp,
                user_id="harvester"
            )
            self.logger.info(f"Response workflow job id: {workflow_job_id}")
        except Exception as e:
            self.logger.error(f"Posting workflow job failed: {e}")
            return None
        return workflow_job_id

    def _get_workflow_job_status(self, workflow_id: str, job_id: str) -> Union[str, None]:
        # Check job status
        try:
            self.logger.info(f"Checking workflow job status of: {job_id}")
            workflow_job_status = get_workflow_job_status(
                server_address=self.server_address,
                auth=self.auth,
                workflow_id=workflow_id,
                job_id=job_id
            )
            self.logger.info(f"Response workflow job status: {workflow_job_status}")
        except Exception as e:
            self.logger.error(f"Checking workflow job status failed: {e}")
            return None
        return workflow_job_status

    def _poll_workflow_job_status(self, workflow_id: str, job_id: str) -> bool:
        tries = 30
        while tries > 0:
            tries -= 1
            self.logger.info(f"Checking the job status after {WAIT_TIME_BETWEEN_POLLS} seconds")
            time.sleep(WAIT_TIME_BETWEEN_POLLS)

            # Check job status
            try:
                self.logger.info(f"Checking workflow job status of: {job_id}")
                workflow_job_status = get_workflow_job_status(
                    server_address=self.server_address,
                    auth=self.auth,
                    workflow_id=workflow_id,
                    job_id=job_id
                )
                if not workflow_job_status:
                    return False
                self.logger.info(f"Response workflow job status: {workflow_job_status}")
            except Exception as e:
                self.logger.error(f"Checking workflow job status failed: {e}")
                return False

            if workflow_job_status == "SUCCESS":
                return True

            # TODO: Fix may be needed here
            # When Stopped loop 3 more times.
            # Sometimes the STOPPED changes to SUCCESS
            if workflow_job_status == "STOPPED" and tries > 3:
                tries = 3
