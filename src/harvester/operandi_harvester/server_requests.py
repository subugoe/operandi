from requests import get, post
from requests.auth import HTTPBasicAuth
from os.path import join, dirname

__all__ = [
    "get_workflow_job",
    "get_workflow_job_status",
    "get_workspace",
    "post_workflow_job",
    "post_workflow_script",
    "post_workspace",
    "post_workspace_url",
]


def __receive_file(response, download_path):
    with open(download_path, 'wb') as filePtr:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                filePtr.write(chunk)


def post_workspace_url(
        server_address: str,
        auth: HTTPBasicAuth,
        mets_url: str
):
    req_url = f'{server_address}/workspace/import_external?mets_url={mets_url}'
    req_headers = {'accept': 'application/json'}
    response = post(url=req_url, headers=req_headers, auth=auth)
    workspace_id = response.json()['resource_id']
    return workspace_id


def post_workspace(
        server_address: str,
        auth: HTTPBasicAuth,
        ocrd_zip_name: str
):
    ocrd_zip_path = f"{dirname(__file__)}/assets/{ocrd_zip_name}"
    workspace_zip = {'workspace': open(f'{ocrd_zip_path}', 'rb')}
    req_url = f'{server_address}/workspace'
    response = post(url=req_url, files=workspace_zip, auth=auth)
    workspace_id = response.json()['resource_id']
    return workspace_id


def post_workflow_script(
        server_address: str,
        auth: HTTPBasicAuth,
        nf_script_name: str
):
    nextflow_script_path = f"{dirname(__file__)}/assets/{nf_script_name}"
    nextflow_file = {'nextflow_script': open(f'{nextflow_script_path}', 'rb')}
    req_url = f'{server_address}/workflow'
    response = post(url=req_url, files=nextflow_file, auth=auth)
    workflow_id = response.json()['resource_id']
    return workflow_id


def post_workflow_job(
        server_address: str,
        auth: HTTPBasicAuth,
        workflow_id: str,
        workspace_id: str,
        input_file_grp: str
):
    req_url = f'{server_address}/workflow/{workflow_id}'
    req_data = {
        'workspace_id': f'{workspace_id}',
        'input_file_grp': f'{input_file_grp}'
    }
    req_headers = {'accept': 'application/json'}
    response = post(url=req_url, json=req_data, headers=req_headers, auth=auth)
    print(response.__dict__)
    workflow_job_id = response.json()['resource_id']
    return workflow_job_id


def get_workspace(
        server_address: str,
        auth: HTTPBasicAuth,
        workspace_id: str,
        download_path: str
):
    req_url = f'{server_address}/workspace/{workspace_id}'
    req_headers = {'accept': 'application/vnd.ocrd+zip'}
    response = get(url=req_url, headers=req_headers, auth=auth)

    local_filename = f"{workspace_id}.ocrd.zip"
    download_path = join(download_path, local_filename)
    __receive_file(response=response, download_path=download_path)


def get_workflow_job(
        server_address: str,
        auth: HTTPBasicAuth,
        workflow_id: str,
        job_id: str,
        download_path: str
):
    req_url = f'{server_address}/workflow/{workflow_id}/{job_id}'
    req_headers = {'accept': 'application/vnd.zip'}
    response = get(url=req_url, headers=req_headers, auth=auth)

    local_filename = f"{job_id}.zip"
    download_path = join(download_path, local_filename)
    __receive_file(response=response, download_path=download_path)


def get_workflow_job_status(
        server_address: str,
        auth: HTTPBasicAuth,
        workflow_id: str,
        job_id: str
):
    req_url = f'{server_address}/workflow/{workflow_id}/{job_id}'
    req_headers = {'accept': 'application/json'}
    response = get(url=req_url, headers=req_headers, auth=auth)
    job_status = response.json()['job_state']
    return job_status
