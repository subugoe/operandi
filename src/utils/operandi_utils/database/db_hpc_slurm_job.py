from operandi_utils import call_sync, StateJobSlurm
from .models import DBHPCSlurmJob


async def db_create_hpc_slurm_job(
    workflow_job_id: str, hpc_slurm_job_id: str, hpc_batch_script_path: str, hpc_slurm_workspace_path: str,
    hpc_slurm_job_state: StateJobSlurm = StateJobSlurm.UNSET, details: str = "HPCSlurmJob"
) -> DBHPCSlurmJob:
    db_hpc_slurm_job = DBHPCSlurmJob(
        workflow_job_id=workflow_job_id, hpc_slurm_job_id=hpc_slurm_job_id, hpc_batch_script_path=hpc_batch_script_path,
        hpc_slurm_workspace_path=hpc_slurm_workspace_path, hpc_slurm_job_state=hpc_slurm_job_state, details=details)
    await db_hpc_slurm_job.save()
    return db_hpc_slurm_job


@call_sync
async def sync_db_create_hpc_slurm_job(
    workflow_job_id: str, hpc_slurm_job_id: str, hpc_batch_script_path: str, hpc_slurm_workspace_path: str,
    hpc_slurm_job_state: StateJobSlurm = StateJobSlurm.UNSET, details: str = "HPCSlurmJob"
) -> DBHPCSlurmJob:
    return await db_create_hpc_slurm_job(
        workflow_job_id, hpc_slurm_job_id, hpc_batch_script_path, hpc_slurm_workspace_path, hpc_slurm_job_state,
        details)


async def db_get_hpc_slurm_job(workflow_job_id: str) -> DBHPCSlurmJob:
    db_hpc_slurm_job = await DBHPCSlurmJob.find_one(DBHPCSlurmJob.workflow_job_id == workflow_job_id)
    if not db_hpc_slurm_job:
        raise RuntimeError(f"No DB hpc slurm job entry found for id: {workflow_job_id}")
    return db_hpc_slurm_job


@call_sync
async def sync_db_get_hpc_slurm_job(workflow_job_id: str) -> DBHPCSlurmJob:
    return await db_get_hpc_slurm_job(workflow_job_id)


async def db_update_hpc_slurm_job(find_workflow_job_id: str, **kwargs) -> DBHPCSlurmJob:
    db_hpc_slurm_job = await db_get_hpc_slurm_job(workflow_job_id=find_workflow_job_id)
    model_keys = list(db_hpc_slurm_job.__dict__.keys())
    for key, value in kwargs.items():
        if key not in model_keys:
            raise ValueError(f"Field not available: {key}")
        if key == "workflow_job_id":
            db_hpc_slurm_job.workflow_job_id = value
        elif key == "hpc_slurm_job_id":
            db_hpc_slurm_job.hpc_slurm_job_id = value
        elif key == "hpc_slurm_job_state":
            db_hpc_slurm_job.hpc_slurm_job_state = value
        elif key == "hpc_batch_script_path":
            db_hpc_slurm_job.hpc_batch_script_path = value
        elif key == "hpc_slurm_workspace_path":
            db_hpc_slurm_job.hpc_slurm_workspace_path = value
        elif key == "deleted":
            db_hpc_slurm_job.deleted = value
        else:
            raise ValueError(f"Field not updatable: {key}")
    await db_hpc_slurm_job.save()
    return db_hpc_slurm_job


@call_sync
async def sync_db_update_hpc_slurm_job(find_workflow_job_id: str, **kwargs) -> DBHPCSlurmJob:
    return await db_update_hpc_slurm_job(find_workflow_job_id=find_workflow_job_id, **kwargs)
