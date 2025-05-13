from os import environ
from pathlib import Path
from time import sleep

from operandi_server.constants import (
    DEFAULT_METS_BASENAME, DEFAULT_FILE_GRP, SERVER_WORKFLOW_JOBS_ROUTER, SERVER_WORKSPACES_ROUTER)
from operandi_utils.constants import StateJob
from operandi_utils.rabbitmq import RABBITMQ_QUEUE_HPC_DOWNLOADS, RABBITMQ_QUEUE_HARVESTER, RABBITMQ_QUEUE_JOB_STATUSES
from operandi_utils.hpc.constants import HPC_NHR_JOB_TEST_PARTITION
from tests.tests_server.helpers_asserts import assert_response_status_code

OPERANDI_SERVER_BASE_DIR = environ.get("OPERANDI_SERVER_BASE_DIR")

def check_job_till_finish(auth_harvester, operandi, workflow_id: str, workflow_job_id: str):
    tries = 60
    job_status = None
    check_job_status_url = f"/workflow/{workflow_id}/{workflow_job_id}"
    while tries > 0:
        tries -= 1
        sleep(60)
        response = operandi.get(url=check_job_status_url, auth=auth_harvester)
        assert_response_status_code(response.status_code, expected_floor=2)
        job_status = response.json()["job_state"]
        if job_status == StateJob.SUCCESS:
            break

        # TODO: Fix may be needed here
        # When failed loop 5 more times.
        # Sometimes the FAILED changes to SUCCESS
        if job_status == StateJob.FAILED and tries > 5:
            tries = 5
    assert job_status == StateJob.SUCCESS


def download_workflow_job_logs(auth_harvester, operandi, workflow_id: str, workflow_job_id: str):
    tries = 60
    get_log_zip_url = f"/workflow/{workflow_id}/{workflow_job_id}/logs"
    while tries > 0:
        tries -= 1
        sleep(30)
        response = operandi.get(url=get_log_zip_url, auth=auth_harvester)
        if response.status_code != 200:
            continue
        assert_response_status_code(response.status_code, expected_floor=2)
        zip_local_path = Path(environ.get("OPERANDI_SERVER_BASE_DIR"), f"{workflow_job_id}.zip")
        with open(zip_local_path, "wb") as filePtr:
            for chunk in response.iter_bytes(chunk_size=1024):
                if chunk:
                    filePtr.write(chunk)
        assert zip_local_path.exists()
        break


def test_full_cycle(auth_harvester, operandi, service_broker, bytes_small_workspace):
    response = operandi.get("/")
    assert response.json()["message"] == "The home page of the OPERANDI Server"

    # Create a background worker for the harvester queue
    service_broker.create_worker_process(RABBITMQ_QUEUE_HARVESTER, "submit_worker")
    # Create a background worker for the job statuses queue
    service_broker.create_worker_process(RABBITMQ_QUEUE_JOB_STATUSES, "status_worker")
    # Create a background worker for the hpc download queue
    service_broker.create_worker_process(RABBITMQ_QUEUE_HPC_DOWNLOADS, "download_worker")

    # Post a workspace zip
    response = operandi.post(url="/workspace", files={"workspace": bytes_small_workspace}, auth=auth_harvester)
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()["resource_id"]

    remove_file_grps_list_default = [
        "OCR-D-BIN", "OCR-D-CROP", "OCR-D-BIN2", "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG",
        "OCR-D-SEG-LINE-RESEG-DEWARP"
    ]

    remove_file_grps_list_odem = [
        "OCR-D-BINPAGE", "OCR-D-SEG-PAGE-ANYOCR", "OCR-D-DENOISE-OCROPY", "OCR-D-DESKEW-OCROPY",
        "OCR-D-SEG-BLOCK-TESSERACT", "OCR-D-SEGMENT-REPAIR", "OCR-D-CLIP", "OCR-D-SEGMENT-OCROPY", "OCR-D-DEWARP"
    ]

    # Post workflow job
    workflow_id = "default_workflow_with_MS"
    input_file_grp = DEFAULT_FILE_GRP
    req_data = {
        "workflow_id": workflow_id,
        "workflow_args": {
            "workspace_id": workspace_id,
            "input_file_grp": input_file_grp,
            "remove_file_grps": "",
            "preserve_file_grps": f"{input_file_grp},OCR-D-OCR",
            "mets_name": DEFAULT_METS_BASENAME
        },
        "sbatch_args": {"partition": HPC_NHR_JOB_TEST_PARTITION, "cpus": 8, "ram": 32}
    }
    response = operandi.post(url=f"/workflow/{workflow_id}", json=req_data, auth=auth_harvester)
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_job_id = response.json()["resource_id"]

    check_job_till_finish(auth_harvester, operandi, workflow_id, workflow_job_id)
    download_workflow_job_logs(auth_harvester, operandi, workflow_id, workflow_job_id)

    ws_dir = Path(OPERANDI_SERVER_BASE_DIR, SERVER_WORKSPACES_ROUTER, workspace_id)
    assert ws_dir.exists()
    assert Path(ws_dir, input_file_grp).exists()
    assert Path(ws_dir, "OCR-D-OCR").exists()

    # Check if file groups not mentioned in preserve_file_grps are removed
    for file_group in remove_file_grps_list_default:
        assert not Path(ws_dir, file_group).exists()

    wf_job_dir = Path(OPERANDI_SERVER_BASE_DIR, SERVER_WORKFLOW_JOBS_ROUTER, workflow_job_id)
    assert wf_job_dir.exists()
    assert Path(wf_job_dir, "work").exists
    assert Path(wf_job_dir, workspace_id, input_file_grp).exists()
    assert Path(wf_job_dir, workspace_id, "OCR-D-OCR").exists()
