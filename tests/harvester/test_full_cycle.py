from os.path import join
from time import sleep

from operandi_harvester import Harvester
from tests.constants import OPERANDI_TESTS_LOCAL_DIR
from tests.server.helpers_asserts import assert_response_status_code


def test_full_cycle(auth, operandi, service_broker, bytes_workflow1, bytes_workspace1):
    response = operandi.get('/')
    assert response.json()['message'] == "The home page of the OPERANDI Server"

    # Create a background service worker
    service_broker.create_worker_process(
        queue_name="operandi-for-harvester"
    )

    """
    harvester = Harvester(
        server_address=OPERANDI_LOCAL_SERVER_ADDR,
        auth_username=auth[0],
        auth_password=auth[1]
    )
    harvester.harvest_once_dummy()
    """

    # Post a workflow script
    response = operandi.post(
        url="/workflow",
        files={"nextflow_script": bytes_workflow1},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_id = response.json()['resource_id']

    # Post a workspace zip
    response = operandi.post(
        url="/workspace",
        files={"workspace": bytes_workspace1},
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workspace_id = response.json()['resource_id']

    # Post workflow job
    user_id = "harvester"
    input_file_grp = "OCR-D-IMG"
    req_data = {
        'workflow_id': f'{workflow_id}',
        'workspace_id': f'{workspace_id}',
        'input_file_grp': f'{input_file_grp}'
    }
    response = operandi.post(
        url=f"/workflow/run_workflow/{user_id}",
        headers={'accept': 'application/json'},
        json=req_data,
        auth=auth
    )
    assert_response_status_code(response.status_code, expected_floor=2)
    workflow_job_id = response.json()['resource_id']

    tries = 30
    job_status = None
    while tries > 0:
        sleep(15)
        response = operandi.get(
            url=f"/workflow/{workflow_id}/{workflow_job_id}",
            headers={'accept': 'application/json'},
            auth=auth
        )
        assert_response_status_code(response.status_code, expected_floor=2)
        job_status = response.json()['job_state']
        if job_status in ["STOPPED", "SUCCESS"]:
            break
        tries -= 1
    assert job_status == "SUCCESS"

    response = operandi.get(
        url=f"/workflow/{workflow_id}/{workflow_job_id}",
        headers={'accept': 'application/vnd.zip'},
        auth=auth
    )
    zip_local_path = join(OPERANDI_TESTS_LOCAL_DIR, f"{workflow_job_id}.ocrd.zip")
    with open(zip_local_path, 'wb') as filePtr:
        for chunk in response.iter_bytes(chunk_size=1024):
            if chunk:
                filePtr.write(chunk)
