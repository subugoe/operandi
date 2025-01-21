from datetime import datetime
from typing import List, Optional
from operandi_utils import call_sync
from operandi_utils.constants import StateJob
from operandi_utils.database.models import DBWorkflowJob


async def db_create_workflow_job(
    user_id: str, job_id: str, job_dir: str, job_state: StateJob, workflow_id: str, workspace_id: str,
    details: str = "Workflow-Job"
) -> DBWorkflowJob:
    db_workflow_job = DBWorkflowJob(
        user_id=user_id,
        job_id=job_id,
        job_dir=job_dir,
        job_state=job_state,
        workflow_id=workflow_id,
        workspace_id=workspace_id,
        datetime=datetime.now(),
        details=details
    )
    await db_workflow_job.save()
    return db_workflow_job


@call_sync
async def sync_db_create_workflow_job(
    user_id: str, job_id: str, job_dir: str, job_state: StateJob, workflow_id: str, workspace_id: str,
    details: str = "Workflow-Job",
) -> DBWorkflowJob:
    return await db_create_workflow_job(user_id, job_id, job_dir, job_state, workflow_id, workspace_id, details)


async def db_get_workflow_job(job_id: str) -> DBWorkflowJob:
    db_workflow_job = await DBWorkflowJob.find_one(DBWorkflowJob.job_id == job_id)
    if not db_workflow_job:
        raise RuntimeError(f"No DB workflow job entry found for id: {job_id}")
    return db_workflow_job


async def db_get_all_workflow_jobs_by_user(
    user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, hide_deleted: bool = True
) -> List[DBWorkflowJob]:
    query = {"user_id": user_id}
    if start_date or end_date:
        query["datetime"] = {}
        if start_date:
            query["datetime"]["$gte"] = start_date
        if end_date:
            query["datetime"]["$lte"] = end_date
    if hide_deleted:
        query["deleted"] = False
    db_workflow_jobs = await DBWorkflowJob.find_many(query).to_list()
    return db_workflow_jobs


@call_sync
async def sync_db_get_workflow_job(job_id: str) -> DBWorkflowJob:
    return await db_get_workflow_job(job_id)


async def db_update_workflow_job(find_job_id: str, **kwargs) -> DBWorkflowJob:
    db_workflow_job = await db_get_workflow_job(job_id=find_job_id)
    model_keys = list(db_workflow_job.__dict__.keys())
    for key, value in kwargs.items():
        if key not in model_keys:
            raise ValueError(f"Field not available: {key}")
        if key == "job_id":
            db_workflow_job.job_id = value
        elif key == "job_dir":
            db_workflow_job.job_dir = value
        elif key == "job_state":
            db_workflow_job.job_state = value
        elif key == "workflow_id":
            db_workflow_job.workflow_id = value
        elif key == "workspace_id":
            db_workflow_job.workspace_id = value
        elif key == "workflow_dir":
            db_workflow_job.workflow_dir = value
        elif key == "workspace_dir":
            db_workflow_job.workspace_dir = value
        elif key == "hpc_slurm_job_id":
            db_workflow_job.hpc_slurm_job_id = value
        elif key == "deleted":
            db_workflow_job.deleted = value
        elif key == "details":
            db_workflow_job.details = value
        else:
            raise ValueError(f"Field not updatable: {key}")
    await db_workflow_job.save()
    return db_workflow_job


@call_sync
async def sync_db_update_workflow_job(find_job_id: str, **kwargs) -> DBWorkflowJob:
    return await db_update_workflow_job(find_job_id=find_job_id, **kwargs)

@call_sync
async def sync_db_get_all_workflow_jobs_by_user(
    user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, hide_deleted: bool = True
) -> List[DBWorkflowJob]:
    return await db_get_all_workflow_jobs_by_user(user_id, start_date, end_date, hide_deleted)
