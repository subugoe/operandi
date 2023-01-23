import requests
from .utils import parse_resource_id


def post_workspace_url(server_address: str, mets_url: str):
    req_url = f'{server_address}/workspace/import_external?mets_url={mets_url}'
    req_headers = {'content-Type': 'application/json'}
    response = requests.post(url=req_url, headers=req_headers)
    workspace_id = parse_resource_id(response.json())
    return workspace_id


def post_workflow_job(server_address: str, workflow_id: str, workspace_id: str):
    req_url = f'{server_address}/workflow/{workflow_id}'
    req_data = {
        'workspace_id': f'{workspace_id}',
        'workflow_parameters': {
            'mets': 'mets.xml',
            'input_group': 'DEFAULT'
        }
    }
    req_headers = {'content-Type': 'application/json'}
    response = requests.post(url=req_url, json=req_data, headers=req_headers)
    workflow_job_id = parse_resource_id(response.json())
    return workflow_job_id


def get_workflow_job_status(server_address: str, workflow_id: str, job_id: str):
    req_url = f'{server_address}/workflow/{workflow_id}/{job_id}'
    req_headers = {'content-Type': 'application/json'}
    response = requests.get(url=req_url, headers=req_headers)
    # This gets the entire job_resource
    job_resource = response.json()
    job_status = job_resource['job_state']
    return job_status
