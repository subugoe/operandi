import logging
from typing import List, Union

from fastapi import (
    APIRouter,
    Depends,
    Header,
    UploadFile,
)
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_server.exceptions import ResponseException
from operandi_server.managers import (
    WorkflowManager,
    WorkspaceManager
)
from operandi_server.models import (
    WorkflowRsrc,
    WorkflowJobRsrc
)
from .user import user_login


router = APIRouter(tags=["Workflow"])

logger = logging.getLogger(__name__)
workflow_manager = WorkflowManager()
workspace_manager = WorkspaceManager()
security = HTTPBasic()


# TODO: Refine all the exceptions...
@router.get("/workflow")
async def list_workflows(auth: HTTPBasicCredentials = Depends(security)) -> List[WorkflowRsrc]:
    """
    Get a list of existing workflow spaces.
    Each workflow space has a Nextflow script inside.

    Curl equivalent:
    `curl SERVER_ADDR/workflow`
    """
    await user_login(auth)
    workflows = workflow_manager.get_workflows()
    response = []
    for workflow in workflows:
        wf_id, wf_url = workflow
        response.append(WorkflowRsrc.create(workflow_id=wf_id, workflow_url=wf_url))
    return response


@router.get("/workflow/{workflow_id}", response_model=None)
async def get_workflow_script(
        workflow_id: str,
        accept: str = Header(default="application/json"),
        auth: HTTPBasicCredentials = Depends(security)
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
        workflow_script_url = workflow_manager.get_workflow_url(workflow_id)
        workflow_script_path = workflow_manager.get_resource_file(
            workflow_manager.workflow_router,
            workflow_id,
            file_ext=".nf"
        )
    except Exception as e:
        logger.exception(f"Unexpected error in get_workflow_script: {e}")
        # TODO: Don't provide the exception message to the outside world
        raise ResponseException(500, {"error": f"internal server error: {e}"})

    if accept == "text/vnd.ocrd.workflow":
        if not workflow_script_path:
            raise ResponseException(404, {})
        return FileResponse(path=workflow_script_path, filename="workflow_script.nf")

    if not workflow_script_url:
        raise ResponseException(404, {})
    return WorkflowRsrc.create(workflow_id=workflow_id, workflow_url=workflow_script_url)


@router.post("/workflow", responses={"201": {"model": WorkflowRsrc}})
async def upload_workflow_script(
        nextflow_script: UploadFile,
        auth: HTTPBasicCredentials = Depends(security)
) -> WorkflowRsrc:
    """
    Create a new workflow space and upload a Nextflow script inside.
    Returns a `resource_id` with which the uploaded workflow is identified.

    Curl equivalent:
    `curl -X POST SERVER_ADDR/workflow -F nextflow_script=example.nf`
    """

    await user_login(auth)
    try:
        workflow_id, workflow_url = await workflow_manager.create_workflow_space(nextflow_script)
    except Exception as e:
        logger.exception(f"Error in upload_workflow_script: {e}")
        # TODO: Don't provide the exception message to the outside world
        raise ResponseException(500, {"error": f"internal server error: {e}"})

    return WorkflowRsrc.create(workflow_id=workflow_id, workflow_url=workflow_url)


@router.put("/workflow/{workflow_id}", responses={"201": {"model": WorkflowRsrc}})
async def update_workflow_script(
        nextflow_script: UploadFile,
        workflow_id: str,
        auth: HTTPBasicCredentials = Depends(security)
) -> WorkflowRsrc:
    """
    Update an existing workflow script specified with or `workflow_id` or upload a new workflow script.

    Curl equivalent:
    `curl -X PUT SERVER_ADDR/workflow/{workflow_id} -F nextflow_script=example.nf`
    """

    await user_login(auth)
    try:
        workflow_id, updated_workflow_url = await workflow_manager.update_workflow_space(
            file=nextflow_script,
            workflow_id=workflow_id
        )
    except Exception as e:
        logger.exception(f"Error in update_workflow_script: {e}")
        # TODO: Don't provide the exception message to the outside world
        raise ResponseException(500, {"error": f"internal server error: {e}"})

    return WorkflowRsrc.create(workflow_id=workflow_id, workflow_url=updated_workflow_url)

    # Not in the Web API Specification. Will be implemented if needed.
    # TODO: Implement that since we have some sort of dummy security check
    # @router.delete("/workflow/{workflow_id}", responses={"200": {"model": WorkflowRsrc}})
    # async def delete_workflow_space(workflow_id: str) -> WorkflowRsrc:
    #   pass
