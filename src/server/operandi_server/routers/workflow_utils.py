from fastapi import HTTPException, status
from pathlib import Path

from operandi_utils.database import db_get_workflow, db_get_workflow_job
from operandi_utils.database.models import DBWorkflow, DBWorkflowJob
from operandi_utils.oton import OTONConverter, OCRDValidator


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


async def nf_script_uses_mets_server_with_handling(
    logger, nf_script_path: str, search_string: str = "params.mets_socket"
) -> bool:
    try:
        with open(nf_script_path) as nf_file:
            line = nf_file.readline()
            while line:
                if search_string in line:
                    return True
                line = nf_file.readline()
            return False
    except Exception as error:
        message = "Failed to identify whether a mets server is used or not in the provided Nextflow workflow."
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)


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
