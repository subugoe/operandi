from datetime import datetime
from typing import List, Optional
from operandi_utils import call_sync
from .models import DBWorkflow


# TODO: This also updates to satisfy the PUT method in the Workflow Manager - fix this
async def db_create_workflow(
    user_id: str, workflow_id: str, workflow_dir: str, workflow_script_base: str, workflow_script_path: str,
    uses_mets_server: bool, executable_steps: List[str], producible_file_groups: List[str], details: str = "Workflow"
) -> DBWorkflow:
    try:
        db_workflow = await db_get_workflow(workflow_id)
    except RuntimeError:
        db_workflow = DBWorkflow(
            user_id=user_id,
            workflow_id=workflow_id,
            workflow_dir=workflow_dir,
            workflow_script_base=workflow_script_base,
            workflow_script_path=workflow_script_path,
            uses_mets_server=uses_mets_server,
            executable_steps=executable_steps,
            producible_file_groups=producible_file_groups,
            datetime=datetime.now(),
            details=details
        )
    else:
        db_workflow.user_id = user_id
        db_workflow.workflow_id = workflow_id
        db_workflow.workflow_dir = workflow_dir
        db_workflow.workflow_script_base = workflow_script_base
        db_workflow.workflow_script_path = workflow_script_path
        db_workflow.uses_mets_server = uses_mets_server
        db_workflow.executable_steps = executable_steps
        db_workflow.producible_file_groups = producible_file_groups
        db_workflow.details = details
    await db_workflow.save()
    return db_workflow


@call_sync
async def sync_db_create_workflow(
    user_id: str, workflow_id: str, workflow_dir: str, workflow_script_base: str, workflow_script_path: str,
    uses_mets_server: bool, executable_steps: List[str], producible_file_groups: List[str], details: str = "Workflow"
) -> DBWorkflow:
    return await db_create_workflow(
        user_id, workflow_id, workflow_dir, workflow_script_base, workflow_script_path, uses_mets_server,
        executable_steps, producible_file_groups, details)


async def db_get_workflow(workflow_id: str) -> DBWorkflow:
    db_workflow = await DBWorkflow.find_one(DBWorkflow.workflow_id == workflow_id)
    if not db_workflow:
        raise RuntimeError(f"No DB workflow entry found for id: {workflow_id}")
    return db_workflow

async def db_get_all_workflows_by_user(
    user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, hide_deleted: bool = True
) -> List[DBWorkflow]:
    query = {"user_id": user_id}
    if start_date or end_date:
        query["datetime"] = {}
        if start_date:
            query["datetime"]["$gte"] = start_date
        if end_date:
            query["datetime"]["$lte"] = end_date
    if hide_deleted:
        query["deleted"] = False
    db_workflows = await DBWorkflow.find_many(query).to_list()
    return db_workflows

@call_sync
async def sync_db_get_workflow(workflow_id: str) -> DBWorkflow:
    return await db_get_workflow(workflow_id)


async def db_update_workflow(find_workflow_id: str, **kwargs) -> DBWorkflow:
    db_workflow = await db_get_workflow(workflow_id=find_workflow_id)
    model_keys = list(db_workflow.__dict__.keys())
    for key, value in kwargs.items():
        if key not in model_keys:
            raise ValueError(f"Field not available: {key}")
        if key == "workflow_id":
            db_workflow.workflow_id = value
        elif key == "workflow_dir":
            db_workflow.workflow_dir = value
        elif key == "workflow_script_base":
            db_workflow.workflow_script_base = value
        elif key == "workflow_script_path":
            db_workflow.workflow_script_path = value
        elif key == "uses_mets_server":
            db_workflow.uses_mets_server = value
        elif key == "executable_steps":
            db_workflow.executable_steps = value
        elif key == "producible_file_groups":
            db_workflow.producible_file_groups = value
        elif key == "deleted":
            db_workflow.deleted = value
        elif key == "details":
            db_workflow.details = value
        else:
            raise ValueError(f"Field not updatable: {key}")
    await db_workflow.save()
    return db_workflow


@call_sync
async def sync_db_update_workflow(find_workflow_id: str, **kwargs) -> DBWorkflow:
    return await db_update_workflow(find_workflow_id=find_workflow_id, **kwargs)

@call_sync
async def sync_db_get_all_workflows_by_user(
    user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, hide_deleted: bool = True
) -> List[DBWorkflow]:
    return await db_get_all_workflows_by_user(user_id, start_date, end_date, hide_deleted)
