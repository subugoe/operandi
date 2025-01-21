from datetime import datetime
from fastapi import HTTPException, status
from json import dumps
from pathlib import Path
from typing import List, Optional

from operandi_utils.constants import StateJob
from operandi_utils.database import (
    db_get_all_workflows_by_user, db_get_all_workflow_jobs_by_user,
    db_get_workflow, db_get_workflow_job, db_get_workspace
)
from operandi_utils.database.models import DBWorkflow, DBWorkflowJob
from operandi_utils.oton import OTONConverter, OCRDValidator
from operandi_utils.oton.constants import PARAMS_KEY_METS_SOCKET_PATH
from operandi_utils.rabbitmq import RABBITMQ_QUEUE_JOB_STATUSES
from operandi_server.models import WorkflowRsrc, WorkflowJobRsrc


async def get_db_workflow_with_handling(
    logger, workflow_id: str, check_deleted: bool = True, check_local_existence: bool = True
) -> DBWorkflow:
    try:
        db_workflow = await db_get_workflow(workflow_id=workflow_id)
    except RuntimeError as error:
        message = f"Non-existing DB entry for workflow id: {workflow_id}"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    if check_deleted and db_workflow.deleted:
        message = f"Workflow has been deleted: {workflow_id}"
        logger.error(f"{message}")
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=message)
    if check_local_existence and not Path(db_workflow.workflow_script_path).exists:
        message = f"Non-existing local entry workflow id: {workflow_id}"
        logger.error(f"{message}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return db_workflow


async def get_db_workflow_job_with_handling(logger, job_id: str, check_local_existence: bool = True) -> DBWorkflowJob:
    try:
        db_workflow_job = await db_get_workflow_job(job_id)
    except RuntimeError as error:
        message = f"Non-existing DB entry for workflow job id: {job_id}"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    if check_local_existence and not Path(db_workflow_job.job_dir).exists:
        message = f"Non-existing local entry workflow job id: {db_workflow_job}"
        logger.error(f"{message}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return db_workflow_job

# TODO: Find a way to simplify that potentially by getting the metadata from OtoN directly
#  However, what about user defined workflows then?
async def nf_script_extract_metadata_with_handling(logger, nf_script_path: str) -> dict:
    metadata = {"uses_mets_server": False}
    processor_executables: List[str] = []
    file_groups: List[str] = []
    try:
        with open(nf_script_path) as nf_file:
            line = nf_file.readline()
            while line:
                if not metadata["uses_mets_server"] and PARAMS_KEY_METS_SOCKET_PATH in line:
                    metadata["uses_mets_server"] = True
                edited_line = line.replace(")\n", "")
                for word in edited_line.split(' '):
                    if "ocrd-" in word:
                        processor_executables.append(word)
                        break
                    if word.startswith('"') and word.endswith('"'):
                        file_groups.append(word[1:-1])
                        break
                line = nf_file.readline()
        metadata["executable_steps"] = processor_executables
        metadata["producible_file_groups"] = file_groups
    except Exception as error:
        message = "Failed to extract the metadata of the provided Nextflow workflow."
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)
    logger.info(f"Extracted Nextflow workflow metadata: {metadata}")
    return metadata

async def validate_oton_with_handling(logger, ocrd_process_txt_path: str):
    try:
        # Separate validation for refined error logging
        validator = OCRDValidator()
        validator.validate(input_file=ocrd_process_txt_path)
    except ValueError as error:
        message = "Failed to validate the ocrd process workflow txt file"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

async def convert_oton_with_handling(
    logger, ocrd_process_txt_path: str, nf_script_dest_path: str, environment: str, with_mets_server: bool
):
    environments = ["local", "docker", "apptainer"]
    if environment not in environments:
        message = f"Unknown environment value: {environment}. Must be one of: {environments}"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    try:
        converter = OTONConverter()
        converter.convert_oton(str(ocrd_process_txt_path), str(nf_script_dest_path), environment, with_mets_server)
    except ValueError as error:
        message = "Failed to convert ocrd process workflow to nextflow workflow"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

async def get_user_workflows(
    user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, hide_deleted: bool = True
) -> List[WorkflowRsrc]:
    db_workflows = await db_get_all_workflows_by_user(
        user_id=user_id, start_date=start_date, end_date=end_date, hide_deleted=hide_deleted)
    return [WorkflowRsrc.from_db_workflow(db_workflow) for db_workflow in db_workflows]

async def push_status_request_to_rabbitmq(logger, rmq_publisher, job_id: str):
    # Create the job status message to be sent to the RabbitMQ queue
    try:
        job_status_message = {"job_id": f"{job_id}"}
        logger.debug(f"Encoding the job status RabbitMQ message: {job_status_message}")
        encoded_wf_message = dumps(job_status_message).encode(encoding="utf-8")
        logger.debug(f"Pushing to the RabbitMQ queue for job statuses: {RABBITMQ_QUEUE_JOB_STATUSES}")
        rmq_publisher.publish_to_queue(queue_name=RABBITMQ_QUEUE_JOB_STATUSES, message=encoded_wf_message)
    except Exception as error:
        message = "Failed to push status request to RabbitMQ"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

async def get_user_workflow_jobs(
    logger, rmq_publisher, user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
    hide_deleted: bool = True
) -> List[WorkflowJobRsrc]:
    db_workflow_jobs = await db_get_all_workflow_jobs_by_user(
        user_id=user_id, start_date=start_date, end_date=end_date, hide_deleted=hide_deleted)
    response = []
    for db_workflow_job in db_workflow_jobs:
        job_state = db_workflow_job.job_state
        if job_state != StateJob.SUCCESS and job_state != StateJob.FAILED:
            await push_status_request_to_rabbitmq(logger, rmq_publisher, db_workflow_job.job_id)
        db_workflow = await db_get_workflow(db_workflow_job.workflow_id)
        db_workspace = await db_get_workspace(db_workflow_job.workspace_id)
        response.append(WorkflowJobRsrc.from_db_workflow_job(db_workflow_job, db_workflow, db_workspace))
    return response
