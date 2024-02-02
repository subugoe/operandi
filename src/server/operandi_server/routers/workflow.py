import json
import logging
from os.path import join
from shutil import make_archive
import tempfile
from typing import List, Union
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
    UploadFile,
)
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils.database import db_create_workflow, db_create_workflow_job, db_get_workflow, db_get_workflow_job
from operandi_utils.rabbitmq import (
    get_connection_publisher,
    RABBITMQ_QUEUE_JOB_STATUSES,
    RABBITMQ_QUEUE_HARVESTER,
    RABBITMQ_QUEUE_USERS
)
from operandi_server.constants import SERVER_WORKFLOWS_ROUTER, SERVER_WORKFLOW_JOBS_ROUTER, SERVER_WORKSPACES_ROUTER
from operandi_server.files_manager import (
    create_resource_dir,
    delete_resource_dir,
    get_all_resources_url,
    get_resource_local,
    get_resource_url,
    receive_resource
)
from operandi_server.models import SbatchArguments, WorkflowArguments, WorkflowRsrc, WorkflowJobRsrc
from .user import user_login

router = APIRouter(tags=["Workflow"])
logger = logging.getLogger("operandi_server.routers.workflow")

logger.info(f"Trying to connect RMQ Publisher")
rmq_publisher = get_connection_publisher(enable_acks=True)
logger.info(f"RMQPublisher connected")

# TODO: Reconsider this
rmq_publisher.create_queue(queue_name=RABBITMQ_QUEUE_HARVESTER)
rmq_publisher.create_queue(queue_name=RABBITMQ_QUEUE_USERS)
rmq_publisher.create_queue(queue_name=RABBITMQ_QUEUE_JOB_STATUSES)


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
    workflows = get_all_resources_url(SERVER_WORKFLOWS_ROUTER)
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
        workflow_script_url = get_resource_url(resource_router=SERVER_WORKFLOWS_ROUTER, resource_id=workflow_id)
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
    workflow_id, workflow_dir = create_resource_dir(SERVER_WORKFLOWS_ROUTER, resource_id=None)
    nf_script_dest = join(workflow_dir, nextflow_script.filename)
    try:
        await receive_resource(file=nextflow_script, resource_dst=nf_script_dest)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to receive the workflow resource, error: {error}")
    await db_create_workflow(
        workflow_id=workflow_id,
        workflow_dir=workflow_dir,
        workflow_script_path=nf_script_dest,
        workflow_script_base=nextflow_script.filename
    )
    workflow_url = get_resource_url(SERVER_WORKFLOWS_ROUTER, workflow_id)
    return WorkflowRsrc.create(workflow_id=workflow_id, workflow_url=workflow_url)


@router.put(path="/workflow/{workflow_id}", responses={"201": {"model": WorkflowRsrc}})
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
        delete_resource_dir(SERVER_WORKFLOWS_ROUTER, workflow_id)
    except FileNotFoundError:
        # Resource not available, nothing to be deleted
        pass

    workflow_id, workflow_dir = create_resource_dir(SERVER_WORKFLOWS_ROUTER, resource_id=workflow_id)
    nf_script_dest = join(workflow_dir, nextflow_script.filename)
    try:
        await receive_resource(file=nextflow_script, resource_dst=nf_script_dest)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to receive the workflow resource, error: {error}")
    await db_create_workflow(
        workflow_id=workflow_id,
        workflow_dir=workflow_dir,
        workflow_script_path=nf_script_dest,
        workflow_script_base=nextflow_script.filename
    )
    workflow_url = get_resource_url(SERVER_WORKFLOWS_ROUTER, workflow_id)
    return WorkflowRsrc.create(workflow_id=workflow_id, workflow_url=workflow_url)


@router.get(path="/workflow/{workflow_id}/{job_id}", responses=None)
async def get_workflow_job_status(
    workflow_id: str,
    job_id: str,
    accept: str = Header(default="application/json"),
    auth: HTTPBasicCredentials = Depends(HTTPBasic())
):
    """
    Get the status of a workflow job specified with `workflow_id` and `job_id`.
    Returns the `workflow_id`, `workspace_id`, `job_id`, and
    one of the following job statuses:
    1) QUEUED - The workflow job is queued for execution.
    2) RUNNING - The workflow job is currently running.
    3) FAILED - The workflow job has failed.
    4) SUCCESS - The workflow job has finished successfully.

    Curl equivalent:
    `curl -X GET SERVER_ADDR/workflow/{workflow_id}/{job_id}`
    """
    await user_login(auth)
    # Create the job status message to be sent to the RabbitMQ queue
    job_status_message = {"job_id": f"{job_id}"}
    logger.info(f"Encoding the job status RabbitMQ message: {job_status_message}")
    encoded_workflow_message = json.dumps(job_status_message)
    logger.info(f"Pushing to the RabbitMQ queue for job statuses: {RABBITMQ_QUEUE_JOB_STATUSES}")
    rmq_publisher.publish_to_queue(queue_name=RABBITMQ_QUEUE_JOB_STATUSES, message=encoded_workflow_message)
    try:
        wf_job_db = await db_get_workflow_job(job_id)
    except RuntimeError:
        raise HTTPException(status_code=404, detail=f"No workflow job found for id: {job_id}")
    job_state = wf_job_db.job_state

    try:
        wf_job_local = get_resource_local(SERVER_WORKFLOW_JOBS_ROUTER, resource_id=wf_job_db.job_id)
        wf_job_url = get_resource_url(SERVER_WORKFLOW_JOBS_ROUTER, resource_id=wf_job_db.job_id)
        workflow_url = get_resource_url(SERVER_WORKFLOWS_ROUTER, resource_id=wf_job_db.workflow_id)
        workspace_url = get_resource_url(SERVER_WORKSPACES_ROUTER, resource_id=wf_job_db.workspace_id)
    except Exception as e:
        logger.exception(f"Unexpected error in get_workflow_job: {e}")
        # TODO: Don't provide the exception message to the outside world
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

    if accept == "application/vnd.zip":
        tempdir = tempfile.mkdtemp(prefix="ocrd-wf-job-zip-")
        job_archive_path = make_archive(
            base_name=f"{tempdir}/{job_id}",
            format="zip",
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


# TODO: Refine the exceptions, and further refactor
@router.post(path="/workflow/{workflow_id}", responses=None)
async def submit_to_rabbitmq_queue(
    workflow_id: str,
    workflow_args: WorkflowArguments,
    sbatch_args: SbatchArguments,
    auth: HTTPBasicCredentials = Depends(HTTPBasic())
):
    try:
        user_action = await user_login(auth)
        user_account_type = user_action.account_type
    except Exception as error:
        logger.error(f"Authentication error: {error}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
            detail=f"Invalid login credentials or unapproved account."
        )

    try:
        # Extract sbatch arguments
        logger.info("Extracting sbatch request arguments")
        cpus = sbatch_args.cpus
        ram = sbatch_args.ram

        # Extract workflow arguments
        logger.info("Extracting workflow request arguments")
        workspace_id = workflow_args.workspace_id
        input_file_grp = workflow_args.input_file_grp

        # Create job request parameters
        logger.info("Creating workflow job space")
        job_id, job_dir = create_resource_dir(SERVER_WORKFLOW_JOBS_ROUTER)
        job_state = "QUEUED"

        # Build urls to be sent as a response
        logger.info("Building urls to be sent as a response")
        workspace_url = get_resource_url(resource_router=SERVER_WORKSPACES_ROUTER, resource_id=workspace_id)
        workflow_url = get_resource_url(resource_router=SERVER_WORKFLOWS_ROUTER, resource_id=workflow_id)
        job_url = get_resource_url(resource_router=SERVER_WORKFLOW_JOBS_ROUTER, resource_id=job_id)

        # Save to the workflow job to the database
        logger.info("Saving the workflow job to the database")
        await db_create_workflow_job(
            job_id=job_id,
            job_dir=job_dir,
            job_state=job_state,
            workspace_id=workspace_id,
            workflow_id=workflow_id
        )

        # Create the message to be sent to the RabbitMQ queue
        logger.info("Creating a workflow job RabbitMQ message")
        workflow_processing_message = {
            "workflow_id": f"{workflow_id}",
            "workspace_id": f"{workspace_id}",
            "job_id": f"{job_id}",
            "input_file_grp": f"{input_file_grp}",
            "cpus": f"{cpus}",
            "ram": f"{ram}"
        }
        logger.info(f"Encoding the workflow job RabbitMQ message: {workflow_processing_message}")
        encoded_workflow_message = json.dumps(workflow_processing_message)

        # Send the message to a queue based on the user_id
        if user_account_type == "harvester":
            logger.info(f"Pushing to the RabbitMQ queue for the harvester: {RABBITMQ_QUEUE_HARVESTER}")
            rmq_publisher.publish_to_queue(
                queue_name=RABBITMQ_QUEUE_HARVESTER,
                message=encoded_workflow_message
            )
        else:
            logger.info(f"Pushing to the RabbitMQ queue for the users: {RABBITMQ_QUEUE_USERS}")
            rmq_publisher.publish_to_queue(
                queue_name=RABBITMQ_QUEUE_USERS,
                message=encoded_workflow_message
            )
    except Exception as error:
        logger.error(f"SERVER ERROR: {error}")
        # TODO: Refine exceptions
        raise HTTPException(status_code=500, detail="Internal server error: {error}")

    return WorkflowJobRsrc.create(
        job_id=job_id,
        job_url=job_url,
        workflow_id=workflow_id,
        workflow_url=workflow_url,
        workspace_id=workspace_id,
        workspace_url=workspace_url,
        job_state=job_state
    )
