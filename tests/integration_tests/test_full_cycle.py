from os import environ
from os.path import join
from time import sleep

from operandi_server.constants import DEFAULT_METS_BASENAME, DEFAULT_FILE_GRP
from operandi_utils.constants import StateJob
from operandi_utils.rabbitmq import RABBITMQ_QUEUE_HARVESTER, RABBITMQ_QUEUE_JOB_STATUSES
from operandi_utils.hpc.constants import HPC_JOB_TEST_PARTITION
from tests.tests_server.helpers_asserts import assert_response_status_code


def check_job_till_finish(auth_harvester, operandi, workflow_id: str, workflow_job_id: str):
    tries = 70
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
    get_log_zip_url = f"/workflow/{workflow_id}/{workflow_job_id}/log"
    response = operandi.get(url=get_log_zip_url, auth=auth_harvester)
    zip_local_path = join(environ.get("OPERANDI_SERVER_BASE_DIR"), f"{workflow_job_id}.zip")
    with open(zip_local_path, "wb") as filePtr:
        for chunk in response.iter_bytes(chunk_size=1024):
            if chunk:
                filePtr.write(chunk)


def test_full_cycle(auth_harvester, operandi, service_broker, bytes_small_workspace):
    response = operandi.get("/")
    assert response.json()["message"] == "The home page of the OPERANDI Server"

    # Create a background worker for the harvester queue
    service_broker.create_worker_process(
        queue_name=RABBITMQ_QUEUE_HARVESTER, status_checker=False, tunnel_port_executor=22, tunnel_port_transfer=22)
    # Create a background worker for the job statuses queue
    service_broker.create_worker_process(
        queue_name=RABBITMQ_QUEUE_JOB_STATUSES, status_checker=True, tunnel_port_executor=22, tunnel_port_transfer=22)

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
    workflow_id = "odem_workflow"
    input_file_grp = DEFAULT_FILE_GRP
    req_data = {
        "workflow_id": workflow_id,
        "workflow_args": {
            "workspace_id": workspace_id,
            "input_file_grp": input_file_grp,
            "remove_file_grps": ",".join(remove_file_grps_list_odem),
            "mets_name": DEFAULT_METS_BASENAME
        },
        "sbatch_args": {"partition": HPC_JOB_TEST_PARTITION, "cpus": 2, "ram": 8}
    }
    response = operandi.post(url=f"/workflow/{workflow_id}", json=req_data, auth=auth_harvester)
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_job_id = response.json()["resource_id"]

    check_job_till_finish(auth_harvester, operandi, workflow_id, workflow_job_id)

    # TODO: Fix this, wait for a few secs till the data is transferred from HPC to Operandi Server
    sleep(45)
    download_workflow_job_logs(auth_harvester, operandi, workflow_id, workflow_job_id)
