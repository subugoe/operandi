from fastapi import HTTPException, status
from operandi_utils import call_sync
from .models import DBProcessingStatistics

async def db_create_processing_stats(institution_id: str, user_id: str) -> DBProcessingStatistics:
    db_processing_stats = await DBProcessingStatistics.find_one(
        DBProcessingStatistics.institution_id == institution_id,
        DBProcessingStatistics.user_id == user_id)

    if db_processing_stats:
        raise RuntimeError(
            f"DB processing statistics entry already exists for user_id: {user_id}, institution_id: {institution_id}")

    db_processing_stats = DBProcessingStatistics(institution_id=institution_id, user_id=user_id)
    await db_processing_stats.save()
    return db_processing_stats

@call_sync
async def sync_db_create_processing_stats(institution_id: str, user_id: str) -> DBProcessingStatistics:
    return await db_create_processing_stats(institution_id, user_id)


async def db_get_processing_stats(user_id: str) -> DBProcessingStatistics:
    db_processing_stats = await DBProcessingStatistics.find_one(DBProcessingStatistics.user_id == user_id)
    if not db_processing_stats:
        raise RuntimeError(f"No DB processing statistics entry found for user id: {user_id}")
    return db_processing_stats


@call_sync
async def sync_db_get_processing_stats(user_id: str) -> DBProcessingStatistics:
    return await db_get_processing_stats(user_id)


async def db_increase_processing_stats(find_user_id: str, **kwargs) -> DBProcessingStatistics:
    db_processing_stats = await db_get_processing_stats(user_id=find_user_id)
    model_keys = list(db_processing_stats.__dict__.keys())
    for key, value in kwargs.items():
        if key not in model_keys:
            raise ValueError(f"Field not available: {key}")
        if value < 0:
            raise ValueError(f"Negative value cannot be used to increase usage statistics for key: {key}")
        if key == "pages_uploaded":
            db_processing_stats.pages_uploaded += value
        elif key == "pages_submitted":
            db_processing_stats.pages_submitted += value
        elif key == "pages_succeed":
            db_processing_stats.pages_succeed += value
        elif key == "pages_cancel":
            db_processing_stats.pages_cancel += value
        elif key == "pages_failed":
            db_processing_stats.failed = +value
        elif key == "pages_downloaded":
            db_processing_stats.pages_downloaded = +value
        else:
            raise ValueError(f"Field not updatable: {key}")
    await db_processing_stats.save()
    return db_processing_stats

async def db_increase_processing_stats_with_handling(logger, find_user_id: str, **kwargs) -> DBProcessingStatistics:
    try:
        db_processing_stats = await db_increase_processing_stats(find_user_id=find_user_id, **kwargs)
    except Exception as error:
        message = f"Failed to update processing statistics. Please contact the administrator, error: {error}"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
    return db_processing_stats

@call_sync
async def sync_db_increase_processing_stats(find_user_id: str, **kwargs) -> DBProcessingStatistics:
    return await db_increase_processing_stats(find_user_id=find_user_id, **kwargs)