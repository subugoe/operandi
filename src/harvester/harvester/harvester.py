import logging
import time

from .constants import (
    VD18_IDS_FILE,
    WAIT_TIME_BETWEEN_SUBMITS,
    LOG_LEVEL,
    LOG_FORMAT,
)

from .server_requests import (
    get_workflow_job_status,
    post_workflow_job,
    post_workspace_url
)

from .utils import (
    build_mets_url,
    file_exists,
    is_url_responsive
)


class Harvester:
    def __init__(self, server_address):
        self.logger = logging.getLogger(__name__)
        logging.getLogger(__name__).setLevel(LOG_LEVEL)
        # Change global logger configuration
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

        self.server_address = server_address
        # The default workflow to be used.
        # This id is received when the default script is posted to the Operandi Server
        self.default_nf_workflow_id = "e25cd96d-75cc-4d0a-863f-0155eba07e0f"
        self.wtbs = WAIT_TIME_BETWEEN_SUBMITS

        self.vd18_file = VD18_IDS_FILE
        if not file_exists(self.vd18_file):
            self.logger.error(f"File does not exist or is not a readable file: {self.vd18_file}")
            exit(1)

    def __harvest_one_mets(self, mets_id):
        if not mets_id:
            return False

        # mets_url = build_mets_url(mets_id)

        # TODO: Hard-coded for testing (takes less time with less things to download)
        mets_url = f"https://content.staatsbibliothek-berlin.de/dc/PPN631277528.mets.xml"

        # Check if the VD18 repository responds to the url
        if not is_url_responsive(mets_url):
            return False

        # Post Workspace URL to get workspace_id
        try:
            self.logger.info(f"Trying to post mets url: {mets_url}")
            workspace_id = post_workspace_url(
                server_address=self.server_address,
                mets_url=mets_url
            )
            self.logger.info(f"Mets was posted successfully. Response workspace_id: {workspace_id}")
        except Exception as e:
            self.logger.error(f"Mets was no posted. Fail reason: {e}")
            return False

        # Post Workflow Job with workflow_id (uploaded before starting the harvester)
        # and workspace_id (got from previous request)
        try:
            self.logger.info(f"Trying to post workflow job with "
                             f"workflow_id: {self.default_nf_workflow_id}, "
                             f"workspace_id: {workspace_id}"
                             )
            workflow_job_id = post_workflow_job(
                server_address=self.server_address,
                workflow_id=self.default_nf_workflow_id,
                workspace_id=workspace_id,
                user_id="harvester"
            )
            self.logger.info(f"Workflow job was posted successfully. Response workflow_job_id: {workflow_job_id}")
        except Exception as e:
            self.logger.error(f"Workflow job was not posted. Fail reason: {e}")
            return False

        secs = 5
        self.logger.info(f"Sleeping for {secs} seconds before checking the job status")
        time.sleep(secs)

        # Check job status
        try:
            self.logger.info(f"Trying to check workflow job status for "
                             f"workflow_id: {self.default_nf_workflow_id}, "
                             f"workflow_job_id: {workflow_job_id}"
                             )
            workflow_job_status = get_workflow_job_status(
                server_address=self.server_address,
                workflow_id=self.default_nf_workflow_id,
                job_id=workflow_job_id
            )
            self.logger.info(f"Workflow job status: {workflow_job_status}")
        except Exception as e:
            self.logger.error(f"Checking workflow job status was unsuccessful. Fail reason: {e}")
            return False

        return True

    def __print_waiting_message(self):
        print(f"INFO: Waiting for few seconds... ", end=" ")
        for i in range(self.wtbs, 0, -1):
            print(f"{i}", end=" ")
            if i == 1:
                print()
            time.sleep(1)

    # TODO: implement proper start and stop mechanisms
    def start_harvesting(self, limit=0):
        self.logger.info(f"Harvesting started with limit:{limit}")
        self.logger.info(f"Mets URL will be submitted every {self.wtbs} seconds.")
        harvested_counter = 0

        # Reads vd18 file line by line
        with open(self.vd18_file, mode="r") as f:
            for line in f:
                if not line:
                    break
                mets_id = line.strip()
                self.__harvest_one_mets(mets_id)
                harvested_counter += 1
                # If the limit is reached stop harvesting
                if harvested_counter == limit:
                    break
                self.__print_waiting_message()

    # TODO: implement proper start and stop mechanisms
    def stop_harvesting(self):
        self.logger.info("Stopped harvesting")
