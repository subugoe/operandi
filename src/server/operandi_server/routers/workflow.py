from datetime import datetime
from json import dumps
from logging import getLogger
from os import unlink
from os.path import join
from pathlib import Path
from shutil import make_archive
from tempfile import mkdtemp
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils import create_db_query
from operandi_utils.constants import AccountType, ServerApiTag, StateJob, StateWorkspace
from operandi_utils.database import (
    db_create_page_stat_with_handling, db_create_workflow, db_create_workflow_job, db_get_hpc_slurm_job,
    db_update_workspace)
from operandi_utils.rabbitmq import get_connection_publisher, RABBITMQ_QUEUE_HARVESTER, RABBITMQ_QUEUE_USERS
from operandi_server.files_manager import LFMInstance, receive_resource
from operandi_server.models import SbatchArguments, WorkflowArguments, WorkflowRsrc, WorkflowJobRsrc
from .workflow_utils import (
    get_db_workflow_job_with_handling,
    get_db_workflow_with_handling,
    get_user_workflows,
    nf_script_extract_metadata_with_handling,
    push_status_request_to_rabbitmq
)
from .workspace_utils import (
    check_if_file_group_exists_with_handling, get_db_workspace_with_handling, find_file_groups_to_remove_with_handling)
from .user_utils import user_auth_with_handling


class RouterWorkflow:
    def __init__(self, production_workflows: List[str]):
        self.logger = getLogger("operandi_server.routers.workflow")

        # The workflows available to all users by default
        self.production_workflows = production_workflows

        self.logger.info(f"Trying to connect RMQ Publisher")
        self.rmq_publisher = get_connection_publisher(enable_acks=True)
        self.logger.info(f"RMQPublisher connected")

        self.router = APIRouter(tags=[ServerApiTag.WORKFLOW])
        self.add_api_routes(self.router)

    def __del__(self):
        if self.rmq_publisher:
            self.rmq_publisher.disconnect()

    def add_api_routes(self, router: APIRouter):
        router.add_api_route(
            path="/workflow", endpoint=self.list_workflows, methods=["GET"],
            status_code=status.HTTP_200_OK, response_model=List[WorkflowRsrc], response_model_exclude_unset=True,
            response_model_exclude_none=True,
            summary="List workflows uploaded by the current user."
        )
        router.add_api_route(
            path="/workflow", endpoint=self.upload_workflow_script, methods=["POST"],
            status_code=status.HTTP_201_CREATED, response_model=WorkflowRsrc, response_model_exclude_unset=True,
            response_model_exclude_none=True,
            summary="Upload a nextflow workflow script. Returns a `resource_id` associated with the uploaded script."
        )
        router.add_api_route(
            path="/batch-workflows", endpoint=self.upload_batch_workflow_scripts, methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            summary="Upload a list of nextflow workflow scripts (limit:5). "
                    "Returns a list of `resource_id`s associated with the uploaded workflows.",
            response_model=None
        )
        router.add_api_route(
            path="/batch-workflow-jobs", endpoint=self.submit_batch_workflow_jobs,
            methods=["POST"], status_code=status.HTTP_201_CREATED, summary="Trigger upto 5 workflow jobs with specified workflows and arguments.",
            response_model=List[WorkflowJobRsrc], response_model_exclude_unset=True, response_model_exclude_none=True
        )
        router.add_api_route(
            path="/workflow/{workflow_id}",
            endpoint=self.submit_to_rabbitmq_queue, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="Run a workflow job with the specified `workflow_id` and arguments in the request body.",
            response_model=WorkflowJobRsrc, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        router.add_api_route(
            path="/workflow/{workflow_id}",
            endpoint=self.download_workflow_script, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Download an existing nextflow workflow script identified with `workflow_id`.",
            response_model=None, response_model_exclude_unset=False, response_model_exclude_none=False
        )
        router.add_api_route(
            path="/workflow-job/{job_id}",
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
        router.add_api_route(
            path="/workflow-job/{job_id}/logs",
            endpoint=self.download_workflow_job_logs, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Download the logs zip of a job identified with `workflow_id` and `job_id`.",
            response_model=None, response_model_exclude_unset=False, response_model_exclude_none=False
        )
        router.add_api_route(
            path="/workflow-job/{job_id}/hpc-log",
            endpoint=self.download_workflow_job_hpc_log, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Download the slurm job log file of the `job_id`.",
            response_model=None, response_model_exclude_unset=False, response_model_exclude_none=False
        )
        router.add_api_route(
            path="/workflow/{workflow_id}",
            endpoint=self.update_workflow_script, methods=["PUT"], status_code=status.HTTP_201_CREATED,
            summary="Update an existing workflow script identified with or `workflow_id` or upload a new script.",
            response_model=WorkflowRsrc, response_model_exclude_unset=True, response_model_exclude_none=True
        )

    async def list_workflows(
        self, auth: HTTPBasicCredentials = Depends(HTTPBasic()),
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[WorkflowRsrc]:
        """
        The expected datetime format: YYYY-MM-DDTHH:MM:SS, for example, 2024-12-01T18:17:15
        """
        current_user = await user_auth_with_handling(self.logger, auth)
        query = create_db_query(current_user.user_id, start_date, end_date, hide_deleted=True)
        return await get_user_workflows(logger=self.logger, query=query)

    async def download_workflow_script(
        self, workflow_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> FileResponse:
        """
        Curl equivalent:
        `curl -X GET SERVER_ADDR/workflow/{workflow_id} -H "accept: text/vnd.ocrd.workflow" -o foo.nf`
        """
        await user_auth_with_handling(self.logger, auth)
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
        py_user_action = await user_auth_with_handling(self.logger, auth)
        workflow_id, workflow_dir = LFMInstance.make_dir_workflow()
        nf_script_dest = join(workflow_dir, nextflow_script.filename)
        try:
            await receive_resource(file=nextflow_script, resource_dst=nf_script_dest)
        except Exception as error:
            message = "Failed to receive the workflow resource"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        nf_metadata = await nf_script_extract_metadata_with_handling(self.logger, nf_script_dest)
        db_workflow = await db_create_workflow(
            user_id=py_user_action.user_id, workflow_id=workflow_id, workflow_dir=workflow_dir,
            workflow_script_path=nf_script_dest, workflow_script_base=nextflow_script.filename,
            uses_mets_server=nf_metadata["uses_mets_server"], executable_steps=nf_metadata["executable_steps"],
            producible_file_groups=nf_metadata["producible_file_groups"], details=details)
        return WorkflowRsrc.from_db_workflow(db_workflow)

    async def update_workflow_script(
        self, nextflow_script: UploadFile, workflow_id: str, details: str = "Nextflow workflow",
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkflowRsrc:
        """
        Curl equivalent:
        `curl -X PUT SERVER_ADDR/workflow/{workflow_id} -F nextflow_script=example.nf`
        """
        py_user_action = await user_auth_with_handling(self.logger, auth)
        if workflow_id in self.production_workflows:
            message = f"Production workflow cannot be replaced. Tried to replace: {workflow_id}"
            self.logger.error(message)
            raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=message)
        LFMInstance.delete_dir_workflow(workflow_id=workflow_id, missing_ok=True)
        workflow_id, workflow_dir = LFMInstance.make_dir_workflow(workflow_id=workflow_id)
        nf_script_dest = join(workflow_dir, nextflow_script.filename)
        try:
            await receive_resource(file=nextflow_script, resource_dst=nf_script_dest)
        except Exception as error:
            message = f"Failed to receive the workflow resource"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        nf_metadata = await nf_script_extract_metadata_with_handling(self.logger, nf_script_dest)
        db_workflow = await db_create_workflow(
            user_id=py_user_action.user_id, workflow_id=workflow_id, workflow_dir=workflow_dir,
            workflow_script_path=nf_script_dest, workflow_script_base=nextflow_script.filename,
            uses_mets_server=nf_metadata["uses_mets_server"], executable_steps=nf_metadata["executable_steps"],
            producible_file_groups=nf_metadata["producible_file_groups"], details=details)
        return WorkflowRsrc.from_db_workflow(db_workflow)

    async def get_workflow_job_status(
        self, job_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkflowJobRsrc:
        """
        Curl equivalent:
        `curl -X GET SERVER_ADDR/workflow/{workflow_id}/{job_id}`
        """
        await user_auth_with_handling(self.logger, auth)

        db_wf_job = await get_db_workflow_job_with_handling(self.logger, job_id=job_id, check_local_existence=True)
        workspace_id = db_wf_job.workspace_id
        db_workspace = await get_db_workspace_with_handling(
            self.logger, workspace_id=workspace_id, check_ready=False, check_deleted=True, check_local_existence=True)
        workflow_id = db_wf_job.workflow_id
        db_workflow = await get_db_workflow_with_handling(
            self.logger, workflow_id=workflow_id, check_deleted=False, check_local_existence=False)

        if db_wf_job.job_state not in [StateJob.SUCCESS, StateJob.FAILED, StateJob.TRANSFERRING_FROM_HPC]:
            await push_status_request_to_rabbitmq(self.logger, self.rmq_publisher, job_id=job_id)

        return WorkflowJobRsrc.from_db_workflow_job(
            db_workflow_job=db_wf_job, db_workflow=db_workflow, db_workspace=db_workspace)

    async def download_workflow_job_logs(
        self, background_tasks: BackgroundTasks, job_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> FileResponse:
        """
        Curl equivalent:
        `curl -X GET SERVER_ADDR/workflow/{workflow_id}/logs -H "accept: application/vnd.zip" -o foo.zip`
        """
        await user_auth_with_handling(self.logger, auth)

        db_wf_job = await get_db_workflow_job_with_handling(self.logger, job_id=job_id, check_local_existence=True)
        job_state = db_wf_job.job_state
        if job_state != StateJob.SUCCESS and job_state != StateJob.FAILED:
            await push_status_request_to_rabbitmq(self.logger, self.rmq_publisher, job_id=job_id)
            message = f"Cannot download logs of a job unless it succeeds or fails: {job_id}"
            self.logger.exception(message)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

        try:
            wf_job_local = LFMInstance.get_dir_workflow_job(workflow_job_id=db_wf_job.job_id)
        except FileNotFoundError as error:
            message = f"Failed to locate the workflow job resource zip"
            self.logger.exception(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        tempdir = mkdtemp(prefix="ocrd-wf-job-zip-")
        job_archive_path = make_archive(base_name=f"{tempdir}/{job_id}", format="zip", root_dir=wf_job_local)
        background_tasks.add_task(unlink, job_archive_path)
        return FileResponse(path=job_archive_path, filename=f"{job_id}.zip", media_type="application/zip")

    async def download_workflow_job_hpc_log(
        self, job_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())):
        await user_auth_with_handling(self.logger, auth)

        db_wf_job = await get_db_workflow_job_with_handling(self.logger, job_id=job_id, check_local_existence=True)
        job_state = db_wf_job.job_state
        if job_state != StateJob.SUCCESS and job_state != StateJob.FAILED:
            await push_status_request_to_rabbitmq(self.logger, self.rmq_publisher, job_id=job_id)
            message = f"Cannot download logs of a job unless it succeeds or fails: {job_id}"
            self.logger.exception(message)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

        try:
            wf_job_local = LFMInstance.get_dir_workflow_job(workflow_job_id=db_wf_job.job_id)
        except FileNotFoundError as error:
            message = f"Failed to locate the workflow job resource zip"
            self.logger.exception(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        db_hpc_slurm_job = await db_get_hpc_slurm_job(workflow_job_id=db_wf_job.job_id)
        slurm_job_log = f"slurm-job-{db_hpc_slurm_job.hpc_slurm_job_id}.txt"
        slurm_job_log_path = Path(wf_job_local, slurm_job_log)
        if not slurm_job_log_path.exists():
            message = f"No slurm job log file was found for job id: {job_id}"
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        return FileResponse(path=slurm_job_log_path, filename=slurm_job_log, media_type="application/text")

    async def submit_to_rabbitmq_queue(
        self, workflow_id: str, workflow_args: WorkflowArguments, sbatch_args: SbatchArguments,
        details: str = "Workflow job", auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ):
        py_user_action = await user_auth_with_handling(self.logger, auth)
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
            # TODO: Verify if the file groups requested to be removed/preserved are in fact
            #  going to be produced in the future by the used workflow
            remove_file_grps = workflow_args.remove_file_grps
            preserve_file_grps = workflow_args.preserve_file_grps
        except Exception as error:
            message = "Failed to parse workflow arguments"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)

        if remove_file_grps and preserve_file_grps:
            message = "`remove_file_grps` and `preserve_file_grps` fields are mutually exclusive. Provide only one."
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)

        # Check the availability and readiness of the workspace to be used
        db_workspace = await get_db_workspace_with_handling(self.logger, workspace_id=workspace_id)
        if not check_if_file_group_exists_with_handling(self.logger, db_workspace, input_file_grp):
            message = f"The file group `{input_file_grp}` does not exist in the workspace: {db_workspace.workspace_id}"
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)

        # Check the availability of the workflow to be used
        db_workflow = await get_db_workflow_with_handling(self.logger, workflow_id=workflow_id)
        if preserve_file_grps:
            self.logger.info(f"Finding file groups to be removed based on the reproducible/preserve file groups")
            remove_file_grps = find_file_groups_to_remove_with_handling(self.logger, db_workspace, preserve_file_grps)
            remove_file_grps = ",".join(remove_file_grps)
            self.logger.info(f"remove_file_grps: {remove_file_grps}")
            list_preserver_file_grps = preserve_file_grps.split(',')
            remove_file_grps_reproducible = []
            for file_group in db_workflow.producible_file_groups:
                if file_group not in list_preserver_file_grps:
                    remove_file_grps_reproducible.append(file_group)
            if len(remove_file_grps_reproducible) > 0:
                if len(remove_file_grps) > 0:
                    remove_file_grps += ","
                remove_file_grps += f"{','.join(remove_file_grps_reproducible)}"
            self.logger.info(f"remove_file_grps including reproducible: {remove_file_grps}")

        try:
            # Create job request parameters
            self.logger.info("Creating workflow job space")
            job_id, job_dir = LFMInstance.make_dir_workflow_job(exists_ok=False)
            job_state = StateJob.QUEUED
        except Exception as error:
            message = "Failed to create workflow job resource"
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
            user_type=user_account_type, job_id=job_id, input_file_grp=input_file_grp,
            remove_file_grps=remove_file_grps, partition=partition, cpus=cpus, ram=ram
        )
        await db_create_page_stat_with_handling(
            logger=self.logger, stat_type="submitted", quantity=db_workspace.pages_amount,
            institution_id=py_user_action.institution_id, user_id=py_user_action.user_id, workspace_id=workspace_id,
            workflow_job_id=job_id)
        return WorkflowJobRsrc.from_db_workflow_job(
            db_workflow_job=db_wf_job, db_workflow=db_workflow, db_workspace=db_workspace)

    def _push_job_to_rabbitmq(
        self, user_type: AccountType, job_id: str, input_file_grp: str, remove_file_grps: str, partition: str,
        cpus: int, ram: int
    ):
        # Create the message to be sent to the RabbitMQ queue
        self.logger.info("Creating a workflow job RabbitMQ message")
        workflow_processing_message = {
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

    async def upload_batch_workflow_scripts(
        self, workflows: List[UploadFile], auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> List[WorkflowRsrc]:
        """
        Curl equivalent:
        `curl -X POST SERVER_ADDR/batch-workflows -F "workflows=@workflow1.nf" -F "workflows=@workflow2.nf" ...`
        """
        py_user_action = await user_auth_with_handling(self.logger, auth)
        if len(workflows) > 5:
            message = "Batch upload exceeds the limit of 5 workflows"
            self.logger.error(message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        workflow_resources = []
        for workflow in workflows:
            try:
                workflow_id, workflow_dir = LFMInstance.make_dir_workflow()
                nf_script_dest = join(workflow_dir, workflow.filename)
                await receive_resource(file=workflow, resource_dst=nf_script_dest)
                nf_metadata = await nf_script_extract_metadata_with_handling(self.logger, nf_script_dest)
                db_workflow = await db_create_workflow(
                    user_id=py_user_action.user_id,
                    workflow_id=workflow_id,
                    workflow_dir=workflow_dir,
                    workflow_script_path=nf_script_dest,
                    workflow_script_base=workflow.filename,
                    uses_mets_server=nf_metadata['uses_mets_server'],
                    executable_steps=nf_metadata['executable_steps'],
                    producible_file_groups=nf_metadata['producible_file_groups'],
                    details=f"Batch uploaded workflow: {workflow.filename}"
                )
                workflow_resources.append(WorkflowRsrc.from_db_workflow(db_workflow))
            except Exception as error:
                message = f"Failed to process workflow {workflow.filename}"
                self.logger.error(f"{message}, error: {error}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        return workflow_resources

    async def submit_batch_workflow_jobs(
        self, workflow_job_requests: List[dict], auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> List[WorkflowJobRsrc]:
        await user_auth_with_handling(self.logger, auth)
        if len(workflow_job_requests) > 5:
            message = "Batch upload exceeds the limit of 5 workflow jobs"
            self.logger.error(message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        workflow_job_resources = []
        for workflow_job_request in workflow_job_requests:
            try:
                workflow_id = workflow_job_request.get("workflow_id")
                workflow_args = WorkflowArguments(**workflow_job_request.get("workflow_args", {}))
                sbatch_args = SbatchArguments(**workflow_job_request.get("sbatch_args", {}))
                details = workflow_job_request.get("details", "Batch workflow job")
                job_result = await self.submit_to_rabbitmq_queue(
                    workflow_id=workflow_id,
                    workflow_args=workflow_args,
                    sbatch_args=sbatch_args,
                    details=details,
                    auth=auth
                )
                workflow_job_resources.append(job_result)
            except Exception as error:
                message = f"Failed to submit workflow job for request {workflow_job_request}: {error}"
                self.logger.error(message)
                continue  # Skip to the next job in the batch
        if not workflow_job_resources:
            message = "Failed to trigger any workflow jobs."
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        return workflow_job_resources
