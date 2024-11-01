from json import dumps
from logging import getLogger
from os import unlink
from os.path import join
from pathlib import Path
from shutil import make_archive, copyfile
from tempfile import mkdtemp
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_404_NOT_FOUND

from operandi_utils import get_nf_workflows_dir
from operandi_utils.constants import AccountType, ServerApiTag, StateJob, StateWorkspace
from operandi_utils.database import (
    db_create_workflow, db_create_workflow_job, db_get_hpc_slurm_job, db_get_workflow, db_update_workspace,
    db_increase_processing_stats_with_handling)
from operandi_utils.oton.converter import OTONConverter
from operandi_utils.rabbitmq import (
    get_connection_publisher, RABBITMQ_QUEUE_JOB_STATUSES, RABBITMQ_QUEUE_HARVESTER, RABBITMQ_QUEUE_USERS)
from operandi_server.constants import SERVER_WORKFLOWS_ROUTER, SERVER_WORKFLOW_JOBS_ROUTER, SERVER_WORKSPACES_ROUTER
from operandi_server.files_manager import (
    create_resource_dir, delete_resource_dir, get_all_resources_url, get_resource_local, get_resource_url,
    receive_resource)
from operandi_server.models import SbatchArguments, WorkflowArguments, WorkflowRsrc, WorkflowJobRsrc
from .workflow_utils import (
    get_db_workflow_job_with_handling, get_db_workflow_with_handling, nf_script_uses_mets_server_with_handling)
from .workspace_utils import check_if_file_group_exists_with_handling, get_db_workspace_with_handling
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

        self.router = APIRouter(tags=[ServerApiTag.WORKFLOW])
        self.router.add_api_route(
            path=f"/workflow", endpoint=self.list_workflows, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get a list of existing nextflow workflows.",
            response_model=List[WorkflowRsrc], response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workflow", endpoint=self.upload_workflow_script, methods=["POST"],
            status_code=status.HTTP_201_CREATED, response_model=WorkflowRsrc, response_model_exclude_unset=True,
            response_model_exclude_none=True,
            summary="Upload a nextflow workflow script. Returns a `resource_id` associated with the uploaded script."
        )
        self.router.add_api_route(
            path="/workflow/{workflow_id}",
            endpoint=self.download_workflow_script, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Download an existing nextflow workflow script identified with `workflow_id`.",
            response_model=None, response_model_exclude_unset=False, response_model_exclude_none=False
        )
        self.router.add_api_route(
            path="/workflow/{workflow_id}",
            endpoint=self.update_workflow_script, methods=["PUT"], status_code=status.HTTP_201_CREATED,
            summary="Update an existing workflow script identified with or `workflow_id` or upload a new script.",
            response_model=WorkflowRsrc, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workflow/{workflow_id}",
            endpoint=self.submit_to_rabbitmq_queue, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="Run a workflow job with the specified `workflow_id` and arguments in the request body.",
            response_model=WorkflowJobRsrc, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workflow/{workflow_id}/{job_id}",
            endpoint=self.get_workflow_job_status, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="""
            Get the state of a job identified with `workflow_id` and `job_id`.
            One of the following job states is returned:
            1) QUEUED - The workflow job is queued for execution.
            2) PENDING - The workflow job is currently waiting for HPC resources
            3) RUNNING - The workflow job is currently running in the HPC environment.
            4) FAILED - The workflow job has failed.
            5) SUCCESS - The workflow job has finished successfully.
            6) UNSET - The workflow job state was not set yet.
            """,
            response_model=WorkflowJobRsrc, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workflow/{workflow_id}/{job_id}/logs",
            endpoint=self.download_workflow_job_logs, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Download the logs zip of a job identified with `workflow_id` and `job_id`.",
            response_model=None, response_model_exclude_unset=False, response_model_exclude_none=False
        )
        self.router.add_api_route(
            path="/workflow/{workflow_id}/{job_id}/hpc-log",
            endpoint=self.download_workflow_job_hpc_log, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Download the slurm job log file of the `job_id`.",
            response_model=None, response_model_exclude_unset=False, response_model_exclude_none=False
        )
        # Added by Faizan
        self.router.add_api_route(
            path="/convert_workflow",
            endpoint=self.convert_txt_to_nextflow,
            methods=["POST"],
            status_code=status.HTTP_200_OK,
            summary="Upload a text file containing a workflow in ocrd process format and convert it to a Nextflow script in the desired format (local/docker)"
        )

    def __del__(self):
        if self.rmq_publisher:
            self.rmq_publisher.disconnect()

    async def _push_status_request_to_rabbitmq(self, job_id: str):
        # Create the job status message to be sent to the RabbitMQ queue
        try:
            job_status_message = {"job_id": f"{job_id}"}
            self.logger.debug(f"Encoding the job status RabbitMQ message: {job_status_message}")
            encoded_wf_message = dumps(job_status_message).encode(encoding="utf-8")
            self.logger.debug(f"Pushing to the RabbitMQ queue for job statuses: {RABBITMQ_QUEUE_JOB_STATUSES}")
            self.rmq_publisher.publish_to_queue(queue_name=RABBITMQ_QUEUE_JOB_STATUSES, message=encoded_wf_message)
        except Exception as error:
            message = "Failed to push status request to RabbitMQ"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

    async def insert_production_workflows(self, production_workflows_dir: Path = get_nf_workflows_dir()):
        wf_detail = "Workflow provided by the Operandi Server"
        self.logger.info(f"Inserting production workflows for Operandi from: {production_workflows_dir}")
        for path in production_workflows_dir.iterdir():
            if not path.is_file():
                self.logger.info(f"Skipping non-file path: {path}")
                continue
            if path.suffix != '.nf':
                self.logger.info(f"Skipping non .nf extension file path: {path}")
                continue
            # path.stem -> file_name
            # path.name -> file_name.ext
            workflow_id, workflow_dir = create_resource_dir(
                SERVER_WORKFLOWS_ROUTER, resource_id=path.stem, exists_ok=True)
            nf_script_dest = join(workflow_dir, path.name)
            copyfile(src=path, dst=nf_script_dest)
            uses_mets_server = await nf_script_uses_mets_server_with_handling(self.logger, nf_script_dest)
            self.logger.info(f"Inserting: {workflow_id}, uses_mets_server: {uses_mets_server}, script path: {nf_script_dest}")
            await db_create_workflow(
                user_id="Operandi Server",
                workflow_id=workflow_id, workflow_dir=workflow_dir, workflow_script_path=nf_script_dest,
                workflow_script_base=path.name, uses_mets_server=uses_mets_server, details=wf_detail)
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
            db_workflow = await db_get_workflow(workflow_id=wf_id)
            response.append(WorkflowRsrc.from_db_workflow(db_workflow))
        return response

    async def download_workflow_script(
        self, workflow_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> FileResponse:
        """
        Curl equivalent:
        `curl -X GET SERVER_ADDR/workflow/{workflow_id} -H "accept: text/vnd.ocrd.workflow" -o foo.nf`
        """
        await self.user_authenticator.user_login(auth)
        db_workflow = await get_db_workflow_with_handling(self.logger, workflow_id=workflow_id)
        return FileResponse(
            path=db_workflow.workflow_script_path,
            filename=f"{workflow_id}.nf",
            media_type="application/nextflow-file"
        )

    async def upload_workflow_script(
        self, nextflow_script: UploadFile, details: str = "Nextflow workflow",
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkflowRsrc:
        """
        Curl equivalent:
        `curl -X POST SERVER_ADDR/workflow -F nextflow_script=example.nf`
        """
        py_user_action = await self.user_authenticator.user_login(auth)
        workflow_id, workflow_dir = create_resource_dir(SERVER_WORKFLOWS_ROUTER, resource_id=None)
        nf_script_dest = join(workflow_dir, nextflow_script.filename)
        try:
            await receive_resource(file=nextflow_script, resource_dst=nf_script_dest)
        except Exception as error:
            message = "Failed to receive the workflow resource"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        uses_mets_server = await nf_script_uses_mets_server_with_handling(self.logger, nf_script_dest)
        db_workflow = await db_create_workflow(
            user_id=py_user_action.user_id, workflow_id=workflow_id, workflow_dir=workflow_dir,
            workflow_script_path=nf_script_dest, workflow_script_base=nextflow_script.filename,
            uses_mets_server=uses_mets_server, details=details)
        return WorkflowRsrc.from_db_workflow(db_workflow)

    async def update_workflow_script(
        self, nextflow_script: UploadFile, workflow_id: str, details: str = "Nextflow workflow",
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkflowRsrc:
        """
        Curl equivalent:
        `curl -X PUT SERVER_ADDR/workflow/{workflow_id} -F nextflow_script=example.nf`
        """
        py_user_action = await self.user_authenticator.user_login(auth)
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
        nf_script_dest = join(workflow_dir, nextflow_script.filename)
        try:
            await receive_resource(file=nextflow_script, resource_dst=nf_script_dest)
        except Exception as error:
            message = f"Failed to receive the workflow resource"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        uses_mets_server = await nf_script_uses_mets_server_with_handling(self.logger, nf_script_dest)
        db_workflow = await db_create_workflow(
            user_id=py_user_action.user_id, workflow_id=workflow_id, workflow_dir=workflow_dir,
            workflow_script_path=nf_script_dest, workflow_script_base=nextflow_script.filename,
            uses_mets_server=uses_mets_server, details=details)
        return WorkflowRsrc.from_db_workflow(db_workflow)

    async def get_workflow_job_status(
        self, workflow_id: str, job_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkflowJobRsrc:
        """
        Curl equivalent:
        `curl -X GET SERVER_ADDR/workflow/{workflow_id}/{job_id}`
        """
        await self.user_authenticator.user_login(auth)

        db_wf_job = await get_db_workflow_job_with_handling(self.logger, job_id=job_id, check_local_existence=True)
        workspace_id = db_wf_job.workspace_id
        db_workspace = await get_db_workspace_with_handling(
            self.logger, workspace_id=workspace_id, check_ready=False, check_deleted=True, check_local_existence=True)
        workflow_id = db_wf_job.workflow_id
        db_workflow = await get_db_workflow_with_handling(
            self.logger, workflow_id=workflow_id, check_deleted=False, check_local_existence=False)

        if db_wf_job.job_state != StateJob.FAILED and db_wf_job.job_state != StateJob.SUCCESS:
            await self._push_status_request_to_rabbitmq(job_id=job_id)

        # TODO: Fix that by getting rid of the FileManager module
        try:
            wf_job_url = get_resource_url(SERVER_WORKFLOW_JOBS_ROUTER, resource_id=db_wf_job.job_id)
            workflow_url = get_resource_url(SERVER_WORKFLOWS_ROUTER, resource_id=workflow_id)
            workspace_url = get_resource_url(SERVER_WORKSPACES_ROUTER, resource_id=workspace_id)
        except Exception as error:
            message = f"Failed to locate the job resource"
            self.logger.exception(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return WorkflowJobRsrc.from_db_workflow_job(
            db_workflow_job=db_wf_job, db_workflow=db_workflow, db_workspace=db_workspace)

    async def download_workflow_job_logs(
        self, background_tasks: BackgroundTasks, workflow_id: str, job_id: str,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> FileResponse:
        """
        Curl equivalent:
        `curl -X GET SERVER_ADDR/workflow/{workflow_id}/logs -H "accept: application/vnd.zip" -o foo.zip`
        """
        await self.user_authenticator.user_login(auth)
        await self._push_status_request_to_rabbitmq(job_id=job_id)

        db_wf_job = await get_db_workflow_job_with_handling(self.logger, job_id=job_id, check_local_existence=True)
        job_state = db_wf_job.job_state
        if job_state != StateJob.SUCCESS and job_state != StateJob.FAILED:
            message = f"Cannot download logs of a job unless it succeeds or fails: {job_id}"
            self.logger.exception(message)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

        try:
            wf_job_local = get_resource_local(SERVER_WORKFLOW_JOBS_ROUTER, resource_id=db_wf_job.job_id)
        except FileNotFoundError as error:
            message = f"Failed to locate the workflow job resource zip"
            self.logger.exception(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        tempdir = mkdtemp(prefix="ocrd-wf-job-zip-")
        job_archive_path = make_archive(base_name=f"{tempdir}/{job_id}", format="zip", root_dir=wf_job_local)
        background_tasks.add_task(unlink, job_archive_path)
        return FileResponse(path=job_archive_path, filename=f"{job_id}.zip", media_type="application/zip")

    async def download_workflow_job_hpc_log(
        self, workflow_id: str, job_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())):
        await self.user_authenticator.user_login(auth)
        await self._push_status_request_to_rabbitmq(job_id=job_id)

        db_wf_job = await get_db_workflow_job_with_handling(self.logger, job_id=job_id, check_local_existence=True)
        job_state = db_wf_job.job_state
        if job_state != StateJob.SUCCESS and job_state != StateJob.FAILED:
            message = f"Cannot download logs of a job unless it succeeds or fails: {job_id}"
            self.logger.exception(message)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

        try:
            wf_job_local = get_resource_local(SERVER_WORKFLOW_JOBS_ROUTER, resource_id=db_wf_job.job_id)
        except FileNotFoundError as error:
            message = f"Failed to locate the workflow job resource zip"
            self.logger.exception(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        db_hpc_slurm_job = await db_get_hpc_slurm_job(workflow_job_id=db_wf_job.job_id)
        slurm_job_log = f"slurm-job-{db_hpc_slurm_job.hpc_slurm_job_id}.txt"
        slurm_job_log_path = Path(wf_job_local, slurm_job_log)
        if not slurm_job_log_path.exists():
            message = f"No slurm job log file was found for job id: {job_id}"
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=message)
        return FileResponse(path=slurm_job_log_path, filename=slurm_job_log, media_type="application/text")

    async def submit_to_rabbitmq_queue(
        self, workflow_id: str, workflow_args: WorkflowArguments, sbatch_args: SbatchArguments,
        details: str = "Workflow job", auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ):
        py_user_action = await self.user_authenticator.user_login(auth)
        user_account_type = py_user_action.account_type

        try:
            partition = sbatch_args.partition
            cpus = sbatch_args.cpus
            ram = sbatch_args.ram
        except Exception as error:
            message = "Failed to parse sbatch arguments"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)

        try:
            workspace_id = workflow_args.workspace_id
            input_file_grp = workflow_args.input_file_grp
            # TODO: Verify if the file groups requested to be removed are in fact
            #  going to be produced in the future by the used workflow
            remove_file_grps = workflow_args.remove_file_grps
        except Exception as error:
            message = "Failed to parse workflow arguments"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)

        # Check the availability and readiness of the workspace to be used
        db_workspace = await get_db_workspace_with_handling(self.logger, workspace_id=workspace_id)
        if not check_if_file_group_exists_with_handling(self.logger, db_workspace, input_file_grp):
            message = f"The file group `{input_file_grp}` does not exist in the workspace: {db_workspace.workspace_id}"
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)

        # Check the availability of the workflow to be used
        db_workflow = await get_db_workflow_with_handling(self.logger, workflow_id=workflow_id)

        try:
            # Create job request parameters
            self.logger.info("Creating workflow job space")
            job_id, job_dir = create_resource_dir(SERVER_WORKFLOW_JOBS_ROUTER)
            job_state = StateJob.QUEUED

            # TODO: Fix that by getting rid of the FileManager module
            # Build urls to be sent as a response
            self.logger.info("Building urls to be sent as a response")
            workspace_url = get_resource_url(resource_router=SERVER_WORKSPACES_ROUTER, resource_id=workspace_id)
            workflow_url = get_resource_url(resource_router=SERVER_WORKFLOWS_ROUTER, resource_id=workflow_id)
            job_url = get_resource_url(resource_router=SERVER_WORKFLOW_JOBS_ROUTER, resource_id=job_id)
        except Exception as error:
            message = "Failed to create or parse local resources"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

        ws_state = StateWorkspace.QUEUED
        self.logger.info(f"Updating the state to {ws_state} of: {workspace_id}")
        db_workspace = await db_update_workspace(find_workspace_id=workspace_id, state=ws_state)

        self.logger.info("Saving the workflow job to the database")
        db_wf_job = await db_create_workflow_job(
            user_id=py_user_action.user_id, job_id=job_id, job_dir=job_dir, job_state=job_state,
            workspace_id=workspace_id, workflow_id=workflow_id, details=details)

        self._push_job_to_rabbitmq(
            user_id=py_user_action.user_id, user_type=user_account_type, workflow_id=workflow_id,
            workspace_id=workspace_id, job_id=job_id, input_file_grp=input_file_grp,
            remove_file_grps=remove_file_grps, partition=partition, cpus=cpus, ram=ram
        )
        await db_increase_processing_stats_with_handling(
            self.logger, find_user_id=py_user_action.user_id, pages_submitted=db_workspace.pages_amount)
        return WorkflowJobRsrc.from_db_workflow_job(
            db_workflow_job=db_wf_job, db_workflow=db_workflow, db_workspace=db_workspace)

    def _push_job_to_rabbitmq(
        self, user_id: str, user_type: AccountType, workflow_id: str, workspace_id: str, job_id: str,
        input_file_grp: str, remove_file_grps: str, partition: str, cpus: int, ram: int
    ):
        # Create the message to be sent to the RabbitMQ queue
        self.logger.info("Creating a workflow job RabbitMQ message")
        workflow_processing_message = {
            "user_id": f"{user_id}",
            "workflow_id": f"{workflow_id}",
            "workspace_id": f"{workspace_id}",
            "job_id": f"{job_id}",
            "input_file_grp": f"{input_file_grp}",
            "remove_file_grps": f"{remove_file_grps}",
            "partition": f"{partition}",
            "cpus": f"{cpus}",
            "ram": f"{ram}"
        }
        self.logger.info(f"Encoding the workflow job RabbitMQ message: {workflow_processing_message}")
        encoded_workflow_message = dumps(workflow_processing_message).encode(encoding="utf-8")

        # Send the message to a queue based on the user type
        if user_type == AccountType.HARVESTER:
            self.logger.info(f"Pushing to the RabbitMQ queue for the harvester: {RABBITMQ_QUEUE_HARVESTER}")
            self.rmq_publisher.publish_to_queue(queue_name=RABBITMQ_QUEUE_HARVESTER, message=encoded_workflow_message)
        elif user_type == AccountType.ADMIN or user_type == AccountType.USER:
            self.logger.info(f"Pushing to the RabbitMQ queue for the users: {RABBITMQ_QUEUE_USERS}")
            self.rmq_publisher.publish_to_queue(queue_name=RABBITMQ_QUEUE_USERS, message=encoded_workflow_message)
        else:
            message = f"The user account type is not valid: {user_type}. Must be one of: {AccountType}"
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

    # Added by Faizan
    async def convert_txt_to_nextflow(self,
                                      file: UploadFile,
                                      dockerized: bool,
                                      auth: HTTPBasicCredentials = Depends(HTTPBasic())):

        # Authenticate the user
        await self.user_authenticator.user_login(auth)

        # Define upload directory
        upload_dir = Path("/tmp/uploaded_files")
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save the uploaded file to the server
        file_path = upload_dir / "tmp.txt"
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Create the output Nextflow file path
        output_file = file_path.with_suffix(".nf")
        # Use the Converter's convert_OtoN function instead of directly calling OCRDValidator
        converter = OTONConverter()
        try:
            # Call the conversion function (this will also perform validation inside)
            if dockerized:
                converter.convert_oton_env_docker(str(file_path), str(output_file))
            else:
                converter.convert_oton_env_local(str(file_path), str(output_file))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Return the generated Nextflow (.nf) file as a response

        return FileResponse(output_file, filename=output_file.name)