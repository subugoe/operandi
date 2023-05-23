import logging
from shutil import make_archive
from typing import List, Union
import tempfile

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
    WorkflowArguments,
    WorkflowRsrc,
    WorkflowJobRsrc
)
from .user import user_login


router = APIRouter(
    tags=["Workflow"],
)

logger = logging.getLogger(__name__)
workflow_manager = WorkflowManager()
security = HTTPBasic()


# TODO: Refine all the exceptions...
@router.get("/workflow")
async def list_workflows(auth: HTTPBasicCredentials = Depends(security)) -> List[WorkflowRsrc]:
    """
    Get a list of existing workflow space urls.
    Each workflow space has a Nextflow script inside.

    curl http://localhost:8000/workflow/
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
    Get the Nextflow script of an existing workflow space.
    Specify your download path with --output

    When tested with FastAPI's interactive API docs / Swagger (e.g. http://127.0.0.1:8000/docs) the
    accept-header is always set to application/json (no matter what is specified in the gui) so it
    can not be used to test getting the workflow as a file. See:
    https://github.com/OCR-D/ocrd-webapi-implementation/issues/2

    curl -X GET http://localhost:8000/workflow/{workflow_id} -H "accept: text/vnd.ocrd.workflow" --output ./nextflow.nf
    """
    await user_login(auth)
    try:
        workflow_script_url = workflow_manager.get_resource(workflow_id, local=False)
        workflow_script_path = workflow_manager.get_resource_file(workflow_id, file_ext=".nf")
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


@router.get("/workflow/{workflow_id}/{job_id}", responses={"200": {"model": WorkflowJobRsrc}}, response_model=None)
async def get_workflow_job(
        workflow_id: str,
        job_id: str,
        accept: str = Header(default="application/json"),
        auth: HTTPBasicCredentials = Depends(security)
) -> Union[WorkflowJobRsrc, FileResponse]:
    """
    Query a job from the database. Used to query if a job is finished or still running

    workflow_id is not needed in this implementation, but it is used in the specification. In this
    implementation each job-id is unique so workflow_id is not necessary. But it could be necessary
    in other implementations for example if a job_id is only unique in conjunction with a
    workflow_id.
    """
    await user_login(auth)
    wf_job_db = await workflow_manager.get_workflow_job(workflow_id, job_id)
    if not wf_job_db:
        raise ResponseException(404, {})

    try:
        wf_job_url = workflow_manager.get_resource_job(wf_job_db.workflow_id, wf_job_db.workflow_job_id, local=False)
        wf_job_local = workflow_manager.get_resource_job(wf_job_db.workflow_id, wf_job_db.workflow_job_id, local=True)
        workflow_url = workflow_manager.get_resource(wf_job_db.workflow_id, local=False)
        workspace_url = WorkspaceManager.static_get_resource(wf_job_db.workspace_id, local=False)
        job_state = wf_job_db.job_state
    except Exception as e:
        logger.exception(f"Unexpected error in get_workflow_job: {e}")
        # TODO: Don't provide the exception message to the outside world
        raise ResponseException(500, {"error": f"internal server error: {e}"})

    if accept == "application/vnd.zip":
        tempdir = tempfile.mkdtemp(prefix="ocrd-wf-job-zip-")
        job_archive_path = make_archive(
            base_name=f'{tempdir}/{job_id}',
            format='zip',
            root_dir=wf_job_local,
        )
        return FileResponse(job_archive_path)

    return WorkflowJobRsrc.create(
        job_id=job_id,
        job_url=wf_job_url,
        workflow_id=workflow_id,
        workflow_url=workflow_url,
        workspace_id=wf_job_db.workspace_id,
        workspace_url=workspace_url,
        job_state=job_state
    )


@router.post("/workflow/{workflow_id}", responses={"201": {"model": WorkflowJobRsrc}})
async def run_workflow(
        workflow_id: str,
        workflow_args: WorkflowArguments,
        auth: HTTPBasicCredentials = Depends(security)
) -> WorkflowJobRsrc:
    """
    Trigger a Nextflow execution by using a Nextflow script with id {workflow_id} on a
    workspace with id {workspace_id}. The OCR-D results are stored inside the {workspace_id}.

    curl -X POST http://localhost:8000/workflow/{workflow_id}?workspace_id={workspace_id}
    """
    await user_login(auth)
    try:
        parameters = await workflow_manager.start_nf_workflow(
            workflow_id=workflow_id,
            workspace_id=workflow_args.workspace_id
        )
    except Exception as e:
        logger.exception(f"Unexpected error in run_workflow: {e}")
        # TODO: Don't provide the exception message to the outside world
        raise ResponseException(500, {"error": f"internal server error: {e}"})

    # Parse parameters for better readability of the code
    job_id = parameters[0]
    job_url = parameters[1]
    job_status = parameters[2]
    workflow_url = parameters[3]
    workspace_url = parameters[4]

    return WorkflowJobRsrc.create(
        job_id=job_id,
        job_url=job_url,
        workflow_id=workflow_id,
        workflow_url=workflow_url,
        workspace_id=workflow_args.workspace_id,
        workspace_url=workspace_url,
        job_state=job_status
    )


@router.post("/workflow", responses={"201": {"model": WorkflowRsrc}})
async def upload_workflow_script(
        nextflow_script: UploadFile,
        auth: HTTPBasicCredentials = Depends(security)
) -> WorkflowRsrc:
    """
    Create a new workflow space. Upload a Nextflow script inside.

    curl -X POST http://localhost:8000/workflow -F nextflow_script=@things/nextflow.nf  # noqa
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
    Update or create a new workflow space. Upload a Nextflow script inside.

    curl -X PUT http://localhost:8000/workflow/{workflow_id} -F nextflow_script=@things/nextflow-simple.nf
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
