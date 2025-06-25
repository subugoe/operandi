from datetime import datetime
from logging import Logger
from typing import Optional
from fastapi import HTTPException, status
from operandi_utils import call_sync
from .models_stats import (
    DBPageStat,
    DBPageStatDownloaded,
    DBPageStatFailed,
    DBPageStatSubmitted,
    DBPageStatSucceeded,
    DBPageStatUploaded
)

PAGE_STAT_TYPE_TO_MODEL = {
    "uploaded": DBPageStatUploaded,
    "downloaded": DBPageStatDownloaded,
    "submitted": DBPageStatSubmitted,
    "succeeded": DBPageStatSucceeded,
    "failed": DBPageStatFailed,
}

async def db_create_page_stat(
    stat_type: str, quantity: int, institution_id: str, user_id: str, workspace_id: str,
    workflow_job_id: Optional[str] = ""
) -> DBPageStat:
    if stat_type not in PAGE_STAT_TYPE_TO_MODEL:
        raise RuntimeError(f"DB page stat type is {stat_type}, must be one of: {list(PAGE_STAT_TYPE_TO_MODEL.keys())}")

    model_data = dict(
        institution_id=institution_id,
        user_id=user_id,
        datetime=datetime.now(),
        workspace_id=workspace_id,
        quantity=quantity,
    )

    model_class = PAGE_STAT_TYPE_TO_MODEL[stat_type]

    if "workflow_job_id" in model_class.__annotations__:
        model_data["workflow_job_id"] = workflow_job_id

    db_page_stat = model_class(**model_data)
    await db_page_stat.save()
    return db_page_stat


@call_sync
async def sync_db_create_page_stat(
    stat_type: str, quantity: int, institution_id: str, user_id: str, workspace_id: str,
    workflow_job_id: Optional[str] = ""
) -> DBPageStat:
    return await db_create_page_stat(stat_type, quantity, institution_id, user_id, workspace_id, workflow_job_id)


async def db_create_page_stat_with_handling(
    logger: Logger, stat_type: str, quantity: int, institution_id: str, user_id: str, workspace_id: str,
    workflow_job_id: Optional[str] = ""
) -> DBPageStat:
    try:
        db_page_stat = await db_create_page_stat(
            stat_type, quantity, institution_id, user_id, workspace_id, workflow_job_id)
    except Exception as error:
        message = (
            f"Failed to create a page stat of type: {stat_type}, quantity: {quantity}, user_id: {user_id}, "
            f"institution_id: {institution_id}, workspace_id: {workspace_id}, workflow_job_id: {workflow_job_id}. "
            f"Please contact the administrator, error: {error}")
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
    return db_page_stat
