from json import dumps
from logging import getLogger
from os.path import join
from pathlib import Path
from shutil import make_archive, copyfile
from tempfile import mkdtemp
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils import get_nf_workflows_dir, StateJob
from operandi_utils.database import (
    db_create_workflow,
    db_create_workflow_job,
    db_get_workflow,
    db_get_workflow_job
)
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
from .user import RouterUser


class RouterWorkflow:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.workflow")
        self.user_authenticator = RouterUser()

        # The workflows available to all users by default
        self.production_workflows = []

        self.logger.info(f"Trying to connect RMQ Publisher")
        self.rmq_publisher = get_connection_publisher(enable_acks=True)
        self.logger.info(f"RMQPublisher connected")

        # TODO: Reconsider the creation of queues here.
        self.rmq_publisher.create_queue(queue_name=RABBITMQ_QUEUE_HARVESTER)
        self.rmq_publisher.create_queue(queue_name=RABBITMQ_QUEUE_USERS)
        self.rmq_publisher.create_queue(queue_name=RABBITMQ_QUEUE_JOB_STATUSES)

        self.router = APIRouter(tags=["Workflow"])
        self.router.add_api_route(
            path="/workflow",
            endpoint=self.list_workflows,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            summary="Get a list of existing nextflow workflows.",
            response_model=List[WorkflowRsrc],
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workflow",
            endpoint=self.upload_workflow_script,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            summary="""
            Upload a nextflow workflow script.
            Returns a `resource_id` associated with the uploaded script.
            """,
            response_model=WorkflowRsrc,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workflow/{workflow_id}",
            endpoint=self.download_workflow_script,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            summary="Download an existing nextflow workflow script identified with `workflow_id`.",
            response_model=None,
            response_model_exclude_unset=False,
            response_model_exclude_none=False
        )
        self.router.add_api_route(
            path="/workflow/{workflow_id}",
            endpoint=self.update_workflow_script,
            methods=["PUT"],
            status_code=status.HTTP_201_CREATED,
            summary="""
            Update an existing workflow script identified with or `workflow_id` or upload a new workflow script.
            """,
            response_model=WorkflowRsrc,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workflow/{workflow_id}",
            endpoint=self.submit_to_rabbitmq_queue,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            summary="""
            Run a workflow job with the specified `workflow_id` and arguments in the request body.
            """,
            response_model=WorkflowJobRsrc,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workflow/{workflow_id}/{job_id}",
            endpoint=self.get_workflow_job_status,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            summary="""
            Get the state of a job identified with `workflow_id` and `job_id`.
            One of the following job states are returned:
            1) QUEUED - The workflow job is queued for execution.
            2) RUNNING - The workflow job is currently running.
            3) FAILED - The workflow job has failed.
            4) SUCCESS - The workflow job has finished successfully.
            """,
            response_model=WorkflowJobRsrc,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workflow/{workflow_id}/{job_id}/logs",
            endpoint=self.download_workflow_job_logs,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            summary="Download the logs zip of a job identified with `workflow_id` and `job_id`.",
            response_model=None,
            response_model_exclude_unset=False,
            response_model_exclude_none=False
        )

    async def _push_status_request_to_rabbitmq(self, job_id: str):
        # Create the job status message to be sent to the RabbitMQ queue
        job_status_message = {"job_id": f"{job_id}"}
        self.logger.debug(f"Encoding the job status RabbitMQ message: {job_status_message}")
        encoded_workflow_message = dumps(job_status_message)
        self.logger.debug(f"Pushing to the RabbitMQ queue for job statuses: {RABBITMQ_QUEUE_JOB_STATUSES}")
        self.rmq_publisher.publish_to_queue(queue_name=RABBITMQ_QUEUE_JOB_STATUSES, message=encoded_workflow_message)

    async def insert_production_workflows(self, production_workflows_dir: Path = get_nf_workflows_dir()):
        for path in production_workflows_dir.iterdir():
            if not path.is_file():
                continue
            if path.suffix != '.nf':
                continue
            # path.stem -> file_name
            # path.name -> file_name.ext
            workflow_id, workflow_dir = create_resource_dir(
                SERVER_WORKFLOWS_ROUTER,
                resource_id=path.stem,
                exists_ok=True
            )
            nf_script_dst = join(workflow_dir, path.name)
            copyfile(src=path, dst=nf_script_dst)
            await db_create_workflow(
                workflow_id=workflow_id,
                workflow_dir=workflow_dir,
                workflow_script_path=nf_script_dst,
                workflow_script_base=path.name
            )
            self.production_workflows.append(workflow_id)

    async def list_workflows(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> List[WorkflowRsrc]:
        """
        Curl equivalent:
        `curl SERVER_ADDR/workflow`
        """
        await self.user_authenticator.user_login(auth)
        workflows = get_all_resources_url(SERVER_WORKFLOWS_ROUTER)
        response = []
        for workflow in workflows:
            wf_id, wf_url = workflow
            response.append(WorkflowRsrc.create(workflow_id=wf_id, workflow_url=wf_url))
        return response

    async def download_workflow_script(
        self,
        workflow_id: str,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> FileResponse:
        """
        Curl equivalent:
        `curl -X GET SERVER_ADDR/workflow/{workflow_id} -H "accept: text/vnd.ocrd.workflow" -o foo.nf`
        """
        await self.user_authenticator.user_login(auth)
        try:
            db_workflow = await db_get_workflow(workflow_id=workflow_id)
        except RuntimeError as error:
            message = f"Non-existing DB entry for workflow id:{workflow_id}"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        except FileNotFoundError as error:
            message = f"Non-existing local entry workflow id:{workflow_id}"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        return FileResponse(
            path=db_workflow.workflow_script_path,
            filename=f"{workflow_id}.nf",
            media_type="application/nextflow-file"
        )

    async def upload_workflow_script(
        self,
        nextflow_script: UploadFile,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkflowRsrc:
        """
        Curl equivalent:
        `curl -X POST SERVER_ADDR/workflow -F nextflow_script=example.nf`
        """
        await self.user_authenticator.user_login(auth)
        workflow_id, workflow_dir = create_resource_dir(SERVER_WORKFLOWS_ROUTER, resource_id=None)
        nf_script_dest = join(workflow_dir, nextflow_script.filename)
        try:
            await receive_resource(file=nextflow_script, resource_dst=nf_script_dest)
        except Exception as error:
            message = "Failed to receive the workflow resource"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        await db_create_workflow(
            workflow_id=workflow_id,
            workflow_dir=workflow_dir,
            workflow_script_path=nf_script_dest,
            workflow_script_base=nextflow_script.filename
        )
        workflow_url = get_resource_url(SERVER_WORKFLOWS_ROUTER, workflow_id)
        return WorkflowRsrc.create(workflow_id=workflow_id, workflow_url=workflow_url)

    async def update_workflow_script(
        self,
        nextflow_script: UploadFile,
        workflow_id: str,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkflowRsrc:
        """
        Curl equivalent:
        `curl -X PUT SERVER_ADDR/workflow/{workflow_id} -F nextflow_script=example.nf`
        """
        await self.user_authenticator.user_login(auth)
        if workflow_id in self.production_workflows:
            message = f"Production workflow cannot be replaced. Tried to replace: {workflow_id}"
            self.logger.error(message)
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=message)
        try:
            delete_resource_dir(SERVER_WORKFLOWS_ROUTER, workflow_id)
        except FileNotFoundError:
            # Resource not available, nothing to be deleted
            pass

        workflow_id, workflow_dir = create_resource_dir(SERVER_WORKFLOWS_ROUTER, resource_id=workflow_id)
        nf_script_dst = join(workflow_dir, nextflow_script.filename)
        try:
            await receive_resource(file=nextflow_script, resource_dst=nf_script_dst)
        except Exception as error:
            message = f"Failed to receive the workflow resource"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        await db_create_workflow(
            workflow_id=workflow_id,
            workflow_dir=workflow_dir,
            workflow_script_path=nf_script_dst,
            workflow_script_base=nextflow_script.filename
        )
        workflow_url = get_resource_url(SERVER_WORKFLOWS_ROUTER, workflow_id)
        return WorkflowRsrc.create(workflow_id=workflow_id, workflow_url=workflow_url)

    async def get_workflow_job_status(
        self,
        workflow_id: str,
        job_id: str,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkflowJobRsrc:
        """
        Curl equivalent:
        `curl -X GET SERVER_ADDR/workflow/{workflow_id}/{job_id}`
        """
        await self.user_authenticator.user_login(auth)
        await self._push_status_request_to_rabbitmq(job_id=job_id)
        try:
            wf_job_db = await db_get_workflow_job(job_id)
        except RuntimeError as error:
            message = f"No workflow job found for id: {job_id}"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        job_state = wf_job_db.job_state
        try:
            wf_job_url = get_resource_url(SERVER_WORKFLOW_JOBS_ROUTER, resource_id=wf_job_db.job_id)
            workflow_url = get_resource_url(SERVER_WORKFLOWS_ROUTER, resource_id=wf_job_db.workflow_id)
            workspace_url = get_resource_url(SERVER_WORKSPACES_ROUTER, resource_id=wf_job_db.workspace_id)
        except Exception as error:
            message = f"Failed to locate the job resource"
            self.logger.exception(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return WorkflowJobRsrc.create(
            job_id=job_id,
            job_url=wf_job_url,
            workflow_id=workflow_id,
            workflow_url=workflow_url,
            workspace_id=wf_job_db.workspace_id,
            workspace_url=workspace_url,
            job_state=job_state
        )

    async def download_workflow_job_logs(
        self,
        workflow_id: str,
        job_id: str,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> FileResponse:
        """
        Curl equivalent:
        `curl -X GET SERVER_ADDR/workflow/{workflow_id}/logs -H "accept: application/vnd.zip" -o foo.zip`
        """
        await self.user_authenticator.user_login(auth)
        await self._push_status_request_to_rabbitmq(job_id=job_id)
        try:
            wf_job_db = await db_get_workflow_job(job_id)
        except RuntimeError as error:
            message = f"No workflow job found for id: {job_id}"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        job_state = wf_job_db.job_state
        if job_state != StateJob.SUCCESS and job_state != StateJob.FAILED:
            message = f"Cannot download logs of a job unless it succeeds or fails: {job_id}"
            self.logger.exception(message)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        try:
            wf_job_local = get_resource_local(SERVER_WORKFLOW_JOBS_ROUTER, resource_id=wf_job_db.job_id)
        except FileNotFoundError as error:
            message = f"Failed to locate the job resource zip"
            self.logger.exception(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        tempdir = mkdtemp(prefix="ocrd-wf-job-zip-")
        job_archive_path = make_archive(
            base_name=f"{tempdir}/{job_id}",
            format="zip",
            root_dir=wf_job_local,
        )
        return FileResponse(
            path=job_archive_path,
            filename=f"{job_id}.zip",
            media_type="application/zip"
        )

    # TODO: Refine this one big method and the exceptions
    async def submit_to_rabbitmq_queue(
        self,
        workflow_id: str,
        workflow_args: WorkflowArguments,
        sbatch_args: SbatchArguments,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ):
        try:
            user_action = await self.user_authenticator.user_login(auth)
            user_account_type = user_action.account_type
        except Exception as error:
            message = f"Invalid login credentials or unapproved account."
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Basic"},
                detail=message
            )
        try:
            # Extract sbatch arguments
            self.logger.info("Extracting sbatch request arguments")
            cpus = sbatch_args.cpus
            ram = sbatch_args.ram

            # Extract workflow arguments
            self.logger.info("Extracting workflow request arguments")
            workspace_id = workflow_args.workspace_id
            input_file_grp = workflow_args.input_file_grp

            # Create job request parameters
            self.logger.info("Creating workflow job space")
            job_id, job_dir = create_resource_dir(SERVER_WORKFLOW_JOBS_ROUTER)
            job_state = StateJob.QUEUED

            # Build urls to be sent as a response
            self.logger.info("Building urls to be sent as a response")
            workspace_url = get_resource_url(resource_router=SERVER_WORKSPACES_ROUTER, resource_id=workspace_id)
            workflow_url = get_resource_url(resource_router=SERVER_WORKFLOWS_ROUTER, resource_id=workflow_id)
            job_url = get_resource_url(resource_router=SERVER_WORKFLOW_JOBS_ROUTER, resource_id=job_id)

            # Save to the workflow job to the database
            self.logger.info("Saving the workflow job to the database")
            await db_create_workflow_job(
                job_id=job_id,
                job_dir=job_dir,
                job_state=job_state,
                workspace_id=workspace_id,
                workflow_id=workflow_id
            )

            # Create the message to be sent to the RabbitMQ queue
            self.logger.info("Creating a workflow job RabbitMQ message")
            workflow_processing_message = {
                "workflow_id": f"{workflow_id}",
                "workspace_id": f"{workspace_id}",
                "job_id": f"{job_id}",
                "input_file_grp": f"{input_file_grp}",
                "cpus": f"{cpus}",
                "ram": f"{ram}"
            }
            self.logger.info(f"Encoding the workflow job RabbitMQ message: {workflow_processing_message}")
            encoded_workflow_message = dumps(workflow_processing_message)

            # Send the message to a queue based on the user_id
            if user_account_type == "harvester":
                self.logger.info(f"Pushing to the RabbitMQ queue for the harvester: {RABBITMQ_QUEUE_HARVESTER}")
                self.rmq_publisher.publish_to_queue(
                    queue_name=RABBITMQ_QUEUE_HARVESTER,
                    message=encoded_workflow_message
                )
            else:
                self.logger.info(f"Pushing to the RabbitMQ queue for the users: {RABBITMQ_QUEUE_USERS}")
                self.rmq_publisher.publish_to_queue(
                    queue_name=RABBITMQ_QUEUE_USERS,
                    message=encoded_workflow_message
                )
        except Exception as error:
            message = "Internal Server Error"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
        return WorkflowJobRsrc.create(
            job_id=job_id,
            job_url=job_url,
            workflow_id=workflow_id,
            workflow_url=workflow_url,
            workspace_id=workspace_id,
            workspace_url=workspace_url,
            job_state=job_state
        )
