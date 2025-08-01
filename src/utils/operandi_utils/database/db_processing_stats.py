from datetime import datetime
from logging import Logger
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from operandi_utils import call_sync
from .models_stats import DBPageStat, DBProcessingStatsTotal, PAGE_STAT_TYPE_TO_MODEL


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


async def db_create_processing_stats(institution_id: str, user_id: str) -> DBProcessingStatsTotal:
    db_processing_stats = await DBProcessingStatsTotal.find_one(
        DBProcessingStatsTotal.institution_id == institution_id,
        DBProcessingStatsTotal.user_id == user_id)

    if db_processing_stats:
        raise RuntimeError(
            f"DB processing statistics entry already exists for user_id: {user_id}, institution_id: {institution_id}")

    db_processing_stats = DBProcessingStatsTotal(
        institution_id=institution_id,
        user_id=user_id,
        pages_uploaded=0,
        pages_submitted=0,
        pages_succeeded=0,
        pages_failed=0,
        pages_downloaded=0,
        pages_cancelled=0
    )
    await db_processing_stats.save()
    return db_processing_stats


async def db_get_processing_stats(
    logger: Logger, user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> DBProcessingStatsTotal:
    db_processing_stats = await db_update_processing_stats(
        logger=logger, user_id=user_id, start_date=start_date, end_date=end_date)
    return db_processing_stats


async def db_update_processing_stats(
    logger: Logger, user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> DBProcessingStatsTotal:
    db_processing_stats = await DBProcessingStatsTotal.find_one(DBProcessingStatsTotal.user_id == user_id)
    if not db_processing_stats:
        raise RuntimeError(f"No DB processing statistics entry found for user id: {user_id}")
    query: Dict[str, Any] = {"user_id": user_id}
    if start_date or end_date:
        query["datetime"] = {}
        if start_date:
            query["datetime"]["$gte"] = start_date
        if end_date:
            query["datetime"]["$lte"] = end_date
    stats = {}
    for stat_type in PAGE_STAT_TYPE_TO_MODEL:
        page_stat_total = 0
        page_stats = await PAGE_STAT_TYPE_TO_MODEL[stat_type].find_many(query).to_list()
        for page_stat in page_stats:
            page_stat_total += page_stat.quantity
        stats[stat_type] = page_stat_total
    db_processing_stats.pages_uploaded = stats["uploaded"]
    db_processing_stats.pages_submitted = stats["submitted"]
    db_processing_stats.pages_succeeded = stats["succeeded"]
    db_processing_stats.pages_failed = stats["failed"]
    db_processing_stats.pages_downloaded = stats["downloaded"]
    db_processing_stats.pages_cancelled = stats["cancelled"]
    await db_processing_stats.save()
    return db_processing_stats
