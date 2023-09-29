import logging
from os.path import join
from typing import List, Union
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_server.constants import WORKFLOWS_ROUTER
from operandi_server.files_manager import (
    create_resource_dir,
    delete_resource_dir,
    get_all_resources_url,
    get_resource_url,
    receive_resource
)
from operandi_server.models import WorkflowRsrc
from operandi_utils.database import db_create_workflow, db_get_workflow
from .user import user_login

router = APIRouter(tags=["Workflow"])
logger = logging.getLogger(__name__)


@router.get("/workflow")
async def list_workflows(
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
) -> List[WorkflowRsrc]:
    """
    Get a list of existing workflow spaces.
    Each workflow space has a Nextflow script inside.

    Curl equivalent:
    `curl SERVER_ADDR/workflow`
    """
    await user_login(auth)
    workflows = get_all_resources_url(WORKFLOWS_ROUTER)
    response = []
    for workflow in workflows:
        wf_id, wf_url = workflow
        response.append(WorkflowRsrc.create(workflow_id=wf_id, workflow_url=wf_url))
    return response


@router.get(path="/workflow/{workflow_id}", response_model=None)
async def get_workflow_script(
        workflow_id: str,
        accept: str = Header(default="application/json"),
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
) -> Union[WorkflowRsrc, FileResponse]:
    """
    Get an existing workflow space script specified with `workflow_id`.
    Depending on the provided header, either a JSON response or a Nextflow file is returned.
    By default, returns a JSON response.

    Curl equivalents:
    `curl -X GET SERVER_ADDR/workflow/{workflow_id} -H "accept: application/json"`
    `curl -X GET SERVER_ADDR/workflow/{workflow_id} -H "accept: text/vnd.ocrd.workflow" -o foo.nf`
    """
    await user_login(auth)
    try:
        db_workflow = await db_get_workflow(workflow_id=workflow_id)
        workflow_script_url = get_resource_url(resource_router=WORKFLOWS_ROUTER, resource_id=workflow_id)
    except RuntimeError:
        raise HTTPException(status_code=404, detail=f"Non-existing DB entry for workflow id:{workflow_id}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Non-existing local entry workflow id:{workflow_id}")
    if accept == "text/vnd.ocrd.workflow":
        return FileResponse(path=db_workflow.workflow_script_path, filename="workflow_script.nf")
    return WorkflowRsrc.create(workflow_id=workflow_id, workflow_url=workflow_script_url)


@router.post("/workflow", responses={"201": {"model": WorkflowRsrc}})
async def upload_workflow_script(
        nextflow_script: UploadFile,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
) -> WorkflowRsrc:
    """
    Create a new workflow space and upload a Nextflow script inside.
    Returns a `resource_id` with which the uploaded workflow is identified.

    Curl equivalent:
    `curl -X POST SERVER_ADDR/workflow -F nextflow_script=example.nf`
    """

    await user_login(auth)
    workflow_id, workflow_dir = create_resource_dir(WORKFLOWS_ROUTER, resource_id=None)
    nf_script_dest = join(workflow_dir, nextflow_script.filename)
    try:
        await receive_resource(file=nextflow_script, resource_dest=nf_script_dest)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to receive the workflow resource, error: {error}")
    await db_create_workflow(
        workflow_id=workflow_id,
        workflow_dir=workflow_dir,
        workflow_script_path=nf_script_dest,
        workflow_script_base=nextflow_script.filename
    )
    workflow_url = get_resource_url(WORKFLOWS_ROUTER, workflow_id)
    return WorkflowRsrc.create(workflow_id=workflow_id, workflow_url=workflow_url)


@router.put("/workflow/{workflow_id}", responses={"201": {"model": WorkflowRsrc}})
async def update_workflow_script(
        nextflow_script: UploadFile,
        workflow_id: str,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
) -> WorkflowRsrc:
    """
    Update an existing workflow script specified with or `workflow_id` or upload a new workflow script.

    Curl equivalent:
    `curl -X PUT SERVER_ADDR/workflow/{workflow_id} -F nextflow_script=example.nf`
    """

    await user_login(auth)
    try:
        delete_resource_dir(WORKFLOWS_ROUTER, workflow_id)
    except FileNotFoundError:
        # Resource not available, nothing to be deleted
        pass

    workflow_id, workflow_dir = create_resource_dir(WORKFLOWS_ROUTER, resource_id=workflow_id)
    nf_script_dest = join(workflow_dir, nextflow_script.filename)
    try:
        await receive_resource(file=nextflow_script, resource_dest=nf_script_dest)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to receive the workflow resource, error: {error}")
    await db_create_workflow(
        workflow_id=workflow_id,
        workflow_dir=workflow_dir,
        workflow_script_path=nf_script_dest,
        workflow_script_base=nextflow_script.filename
    )
    workflow_url = get_resource_url(WORKFLOWS_ROUTER, workflow_id)
    return WorkflowRsrc.create(workflow_id=workflow_id, workflow_url=workflow_url)
