from os import environ
from os.path import join
from time import sleep

from operandi_utils.rabbitmq import RABBITMQ_QUEUE_HARVESTER, RABBITMQ_QUEUE_JOB_STATUSES
from tests.tests_server.helpers_asserts import assert_response_status_code


def test_full_cycle(auth_harvester, operandi, service_broker, bytes_workflow1, bytes_small_workspace):
    response = operandi.get("/")
    assert response.json()["message"] == "The home page of the OPERANDI Server"

    # Create a background worker for the harvester queue
    service_broker.create_worker_process(queue_name=RABBITMQ_QUEUE_HARVESTER, status_checker=False)
    # Create a background worker for the job statuses queue
    service_broker.create_worker_process(queue_name=RABBITMQ_QUEUE_JOB_STATUSES, status_checker=True)

    # Post a workflow script
    response = operandi.post(
        url="/workflow",
        files={"nextflow_script": bytes_workflow1},
        auth=auth_harvester
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()["resource_id"]

    # Post a workspace zip
    response = operandi.post(
        url="/workspace",
        files={"workspace": bytes_small_workspace},
        auth=auth_harvester
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()["resource_id"]

    # Post workflow job
    input_file_grp = "DEFAULT"
    req_data = {
        "workflow_id": workflow_id,
        "workflow_args": {
          "workspace_id": workspace_id,
          "input_file_grp": input_file_grp,
          "mets_name": "mets.xml"
        },
        "sbatch_args": {
          "cpus": 8,
          "ram": 32
        }
    }
    response = operandi.post(
        url=f"/workflow/{workflow_id}",
        json=req_data,
        auth=auth_harvester
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_job_id = response.json()["resource_id"]

    tries = 50
    job_status = None
    while tries > 0:
        tries -= 1
        sleep(30)
        response = operandi.get(
            url=f"/workflow/{workflow_id}/{workflow_job_id}",
            auth=auth_harvester
        )
        assert_response_status_code(response.status_code, expected_floor=2)
        job_status = response.json()["job_state"]
        if job_status == "SUCCESS":
            break

        # TODO: Fix may be needed here
        # When failed loop 5 more times.
        # Sometimes the FAILED changes to SUCCESS
        if job_status == "FAILED" and tries > 5:
            tries = 5

    assert job_status == "SUCCESS"

    # TODO: Fix this, wait for 10 secs till
    #  the data is transferred from HPC to Operandi Server
    sleep(10)
    response = operandi.get(
        url=f"/workflow/{workflow_id}/{workflow_job_id}",
        headers={"accept": "application/vnd.zip"},
        auth=auth_harvester
    )
    zip_local_path = join(environ.get("OPERANDI_SERVER_BASE_DIR"), f"{workflow_job_id}.zip")
    with open(zip_local_path, "wb") as filePtr:
        for chunk in response.iter_bytes(chunk_size=1024):
            if chunk:
                filePtr.write(chunk)


