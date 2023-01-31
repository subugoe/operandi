import requests
from requests.auth import HTTPBasicAuth
from .utils import parse_resource_id, receive_file
from os.path import join


def post_workspace_url(server_address: str, mets_url: str):
    req_url = f'{server_address}/workspace/import_external?mets_url={mets_url}'
    req_headers = {'accept': 'application/json'}
    response = requests.post(url=req_url, headers=req_headers)
    workspace_id = parse_resource_id(response.json())
    return workspace_id


def post_workspace(server_address: str, ocrd_zip_path: str):
    workspace_zip = {'workspace': open(f'{ocrd_zip_path}', 'rb')}
    req_url = f'{server_address}/workspace'
    response = requests.post(url=req_url, files=workspace_zip)
    workspace_id = parse_resource_id(response.json())
    return workspace_id


def post_workflow_script(server_address: str, local_script_path: str):
    nextflow_file = {'nextflow_script': open(f'{local_script_path}', 'rb')}
    req_url = f'{server_address}/workflow'
    req_auth = HTTPBasicAuth('test', 'test')
    response = requests.post(url=req_url, files=nextflow_file, auth=req_auth)
    workflow_id = parse_resource_id(response.json())
    return workflow_id


def post_workflow_job(server_address: str, workflow_id: str, workspace_id: str, user_id: str):
    req_url = f'{server_address}/workflow/run_workflow/{user_id}'
    req_data = {
        'workflow_id': f'{workflow_id}',
        'workspace_id': f'{workspace_id}'
    }
    req_headers = {'accept': 'application/json'}
    response = requests.post(url=req_url, json=req_data, headers=req_headers)
    workflow_job_id = parse_resource_id(response.json())
    return workflow_job_id


def download_workspace(server_address: str, workspace_id: str, download_path: str):
    req_url = f'{server_address}/workspace/{workspace_id}'
    req_headers = {'accept': 'application/vnd.ocrd+zip'}
    response = requests.get(url=req_url, headers=req_headers)

    local_filename = f"{workspace_id}.ocrd.zip"
    download_path = join(download_path, local_filename)
    receive_file(response=response, download_path=download_path)


def download_workflow_job(server_address: str, workflow_id, job_id, download_path: str):
    req_url = f'{server_address}/workflow/{workflow_id}/{job_id}'
    req_headers = {'accept': 'application/vnd.zip'}
    response = requests.get(url=req_url, headers=req_headers)

    local_filename = f"{job_id}.zip"
    download_path = join(download_path, local_filename)
    receive_file(response=response, download_path=download_path)


def get_workflow_job_status(server_address: str, workflow_id: str, job_id: str):
    req_url = f'{server_address}/workflow/{workflow_id}/{job_id}'
    req_headers = {'accept': 'application/json'}
    response = requests.get(url=req_url, headers=req_headers)
    job_resource = response.json()
    job_status = job_resource['job_state']
    return job_status