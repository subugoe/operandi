from typing import List, Union
from beanie import init_beanie, Document
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from os.path import join

from operandi_utils import call_sync
from operandi_utils.database.constants import OPERANDI_DB_NAME
from operandi_utils.database.models import (
    HPCSlurmJobDB,
    WorkflowDB,
    WorkflowJobDB,
    WorkspaceDB,
    UserAccountDB
)


# Having a logger in this scope should be better
# than calling getLogger in every DB method call
logger = logging.getLogger(__name__)


async def initiate_database(db_url: str, db_name: str = None, doc_models: List[Document] = None):
    if db_name is None:
        db_name = OPERANDI_DB_NAME
    if doc_models is None:
        doc_models = [
            HPCSlurmJobDB,
            WorkflowDB,
            WorkspaceDB,
            WorkflowJobDB,
            UserAccountDB
        ]

    if db_url:
        logger.info(f"MongoDB Name: {OPERANDI_DB_NAME}")
        logger.info(f"MongoDB URL: {db_url}")
    else:
        logger.error(f"MongoDB URL is invalid!")
    client = AsyncIOMotorClient(db_url)
    # Documentation: https://beanie-odm.dev/
    await init_beanie(
        database=client.get_default_database(default=db_name),
        document_models=doc_models
    )


@call_sync
async def sync_initiate_database(db_url: str, db_name: str = None, doc_models: List[Document] = None):
    await initiate_database(db_url, db_name, doc_models)


async def get_workflow(workflow_id) -> Union[WorkflowDB, None]:
    return await WorkflowDB.find_one(WorkflowDB.workflow_id == workflow_id)


@call_sync
async def sync_get_workflow(workflow_id) -> Union[WorkflowDB, None]:
    return await get_workflow(workflow_id)


async def get_workflow_path(workflow_id) -> Union[str, None]:
    workflow = await get_workflow(workflow_id)
    if workflow:
        return workflow.workflow_dir
    logger.warning(f"Trying to get a workflow path of a non-existing workflow_id: {workflow_id}")
    return None


@call_sync
async def sync_get_workflow_path(workflow_id) -> Union[str, None]:
    return await get_workflow_path(workflow_id)


async def get_workflow_script_path(workflow_id) -> Union[str, None]:
    workflow = await get_workflow(workflow_id)
    if workflow:
        return workflow.workflow_script_path
    logger.warning(f"Trying to get a workflow script path of a non-existing workflow_id: {workflow_id}")
    return None


@call_sync
async def sync_get_workflow_script_path(workflow_id) -> Union[str, None]:
    return await get_workflow_script_path(workflow_id)


async def get_workflow_job(job_id) -> Union[WorkflowJobDB, None]:
    return await WorkflowJobDB.find_one(WorkflowJobDB.job_id == job_id)


@call_sync
async def sync_get_workflow_job(job_id) -> Union[WorkflowJobDB, None]:
    return await get_workflow_job(job_id)


async def get_hpc_slurm_job(workflow_job_id) -> Union[HPCSlurmJobDB, None]:
    return await HPCSlurmJobDB.find_one(HPCSlurmJobDB.workflow_job_id == workflow_job_id)


@call_sync
async def sync_get_hpc_slurm_job(workflow_job_id) -> Union[HPCSlurmJobDB, None]:
    return await get_hpc_slurm_job(workflow_job_id)


async def get_workspace(workspace_id) -> Union[WorkspaceDB, None]:
    return await WorkspaceDB.find_one(WorkspaceDB.workspace_id == workspace_id)


@call_sync
async def sync_get_workspace(workspace_id) -> Union[WorkspaceDB, None]:
    return await get_workspace(workspace_id)


async def get_workspace_mets_path(workspace_id) -> Union[str, None]:
    workspace = await get_workspace(workspace_id)
    if workspace:
        return workspace.workspace_mets_path
    logger.warning(f"Trying to get a workspace path of a non-existing workspace_id: {workspace_id}")
    return None


@call_sync
async def sync_get_workspace_mets_path(workspace_id) -> Union[str, None]:
    return await get_workspace_mets_path(workspace_id)


async def mark_deleted_workflow(workflow_id) -> bool:
    wf = await get_workflow(workflow_id)
    if wf:
        wf.deleted = True
        await wf.save()
        return True
    logger.warning(f"Trying to flag non-existing workflow as deleted: {workflow_id}")
    return False


@call_sync
async def sync_mark_deleted_workflow(workflow_id) -> bool:
    return await mark_deleted_workflow(workflow_id)


async def mark_deleted_workspace(workspace_id) -> bool:
    """
    set 'WorkspaceDb.deleted' to True

    The api should keep track of deleted workspaces according to the specs.
    This is done with this function and the deleted-property
    """
    ws = await get_workspace(workspace_id)
    if ws:
        ws.deleted = True
        await ws.save()
        return True
    logger.warning(f"Trying to flag non-existing workspace as deleted: {workspace_id}")
    return False


@call_sync
async def sync_mark_deleted_workspace(workspace_id) -> bool:
    return await mark_deleted_workspace(workspace_id)


async def save_workflow(
        workflow_id: str,
        workflow_dir: str,
        workflow_script_base: str,
        workflow_script_path: str
) -> Union[WorkflowDB, None]:

    workflow_db = await get_workflow(workflow_id)
    if not workflow_db:
        workflow_db = WorkflowDB(
            workflow_id=workflow_id,
            workflow_dir=workflow_dir,
            workflow_script_base=workflow_script_base,
            workflow_script_path=workflow_script_path
        )
    else:
        workflow_db.workflow_id = workflow_id
        workflow_db.workflow_dir = workflow_dir
        workflow_db.workflow_script_base = workflow_script_base
        workflow_db.workflow_script_path = workflow_script_path
    await workflow_db.save()
    return workflow_db


@call_sync
async def sync_save_workflow(
        workflow_id: str,
        workflow_dir: str,
        workflow_script_base: str,
        workflow_script_path: str
) -> Union[WorkflowDB, None]:
    return await sync_save_workflow(workflow_id, workflow_dir, workflow_script_base, workflow_script_path)


async def save_workspace(workspace_id: str, workspace_dir: str, bag_info: dict) -> Union[WorkspaceDB, None]:
    """
    save a workspace to the database. Can also be used to update a workspace

    Arguments:
         workspace_id: uid of the workspace which must be available on disk
         workspace_dir: the path of the workspace directory on the local disk
         bag_info: dict with key-value-pairs from bag-info.txt
    """

    bag_info = dict(bag_info)
    mets_basename = "mets.xml"
    workspace_mets_path = join(workspace_dir, mets_basename)
    ocrd_base_version_checksum = None
    ocrd_identifier = bag_info.pop("Ocrd-Identifier")
    bagit_profile_identifier = bag_info.pop("BagIt-Profile-Identifier")
    if "Ocrd-Mets" in bag_info:
        mets_basename = bag_info.pop("Ocrd-Mets")
        workspace_mets_path = join(workspace_dir, mets_basename)  # Replace it with the real path
    if "Ocrd-Base-Version-Checksum" in bag_info:
        ocrd_base_version_checksum = bag_info.pop("Ocrd-Base-Version-Checksum")

    workspace_db = await get_workspace(workspace_id)
    if not workspace_db:
        workspace_db = WorkspaceDB(
            workspace_id=workspace_id,
            workspace_dir=workspace_dir,
            workspace_mets_path=workspace_mets_path,
            mets_basename=mets_basename,
            ocrd_identifier=ocrd_identifier,
            bagit_profile_identifier=bagit_profile_identifier,
            ocrd_base_version_checksum=ocrd_base_version_checksum,
            bag_info_adds=bag_info
        )
    else:
        workspace_db.workspace_dir = workspace_dir
        workspace_db.workspace_mets_path = workspace_mets_path
        workspace_db.mets_basename = mets_basename
        workspace_db.ocrd_identifier = ocrd_identifier
        workspace_db.bagit_profile_identifier = bagit_profile_identifier
        workspace_db.ocrd_base_version_checksum = ocrd_base_version_checksum
        workspace_db.bag_info_adds = bag_info
    await workspace_db.save()
    return workspace_db


@call_sync
async def sync_save_workspace(workspace_id: str, workspace_dir: str, bag_info: dict) -> Union[WorkspaceDB, None]:
    return await save_workspace(workspace_id, workspace_dir, bag_info)


async def save_workflow_job(
        job_id: str,
        job_dir: str,
        job_state: str,
        workflow_id: str,
        workspace_id: str
) -> Union[WorkflowJobDB, None]:
    """
    save a workflow_job to the database. Can also be used to update a workflow_job

    Arguments:
        job_id: id of the workflow job
        workflow_id: id of the workflow the job is/was executing
        workspace_id: id of the workspace the job runs on
        job_dir: the path of the workflow job dir
        job_state: current state of the job
    """
    workflow_job_db = await get_workflow_job(job_id)
    if not workflow_job_db:
        workflow_job_db = WorkflowJobDB(
            job_id=job_id,
            job_dir=job_dir,
            job_state=job_state,
            workflow_id=workflow_id,
            workspace_id=workspace_id
        )
    else:
        workflow_job_db.job_id = job_id
        workflow_job_db.job_dir = job_dir
        workflow_job_db.job_state = job_state
        workflow_job_db.workflow_id = workflow_id
        workflow_job_db.workspace_id = workspace_id
    await workflow_job_db.save()
    return workflow_job_db


@call_sync
async def sync_save_workflow_job(
        job_id: str,
        workflow_id: str,
        workspace_id: str,
        job_dir: str,
        job_state: str
) -> Union[WorkflowJobDB, None]:
    return await save_workflow_job(job_id, workflow_id, workspace_id, job_dir, job_state)


async def save_hpc_slurm_job(
        workflow_job_id: str,
        hpc_slurm_job_id: str,
        hpc_batch_script_path: str,
        hpc_slurm_workspace_path: str,
        hpc_slurm_job_state: str = None
) -> Union[HPCSlurmJobDB, None]:
    hpc_slurm_job_db = await get_hpc_slurm_job(hpc_slurm_job_id)
    if not hpc_slurm_job_db:
        hpc_slurm_job_db = HPCSlurmJobDB(
            workflow_job_id=workflow_job_id,
            hpc_slurm_job_id=hpc_slurm_job_id,
            hpc_batch_script_path=hpc_batch_script_path,
            hpc_slurm_workspace_path=hpc_slurm_workspace_path,
            hpc_slurm_job_state=hpc_slurm_job_state
        )
    else:
        # If not set, just write the old state
        if not hpc_slurm_job_state:
            hpc_slurm_job_state = hpc_slurm_job_db.hpc_slurm_job_state
        hpc_slurm_job_db.workflow_job_id = workflow_job_id
        hpc_slurm_job_db.hpc_slurm_job_id = hpc_slurm_job_id
        hpc_slurm_job_db.hpc_batch_script_path = hpc_batch_script_path
        hpc_slurm_job_db.hpc_slurm_workspace_path = hpc_slurm_workspace_path
        hpc_slurm_job_db.hpc_slurm_job_state = hpc_slurm_job_state
    await hpc_slurm_job_db.save()
    return hpc_slurm_job_db


@call_sync
async def sync_save_hpc_slurm_job(
        workflow_job_id: str,
        hpc_slurm_job_id: str,
        hpc_batch_script_path: str,
        hpc_slurm_workspace_path: str,
        hpc_slurm_job_state: str = None
) -> Union[HPCSlurmJobDB, None]:
    return await save_hpc_slurm_job(
        workflow_job_id,
        hpc_slurm_job_id,
        hpc_batch_script_path,
        hpc_slurm_workspace_path,
        hpc_slurm_job_state
    )


async def set_slurm_job_state(workflow_job_id: str, hpc_slurm_job_state: str) -> bool:
    """
    set state of slurm job to 'state'
    """
    slurm_job = await get_hpc_slurm_job(workflow_job_id=workflow_job_id)
    if slurm_job:
        slurm_job.hpc_slurm_job_state = hpc_slurm_job_state
        await slurm_job.save()
        return True
    logger.warning(f"Trying to set a state to a non-existing slurm job for workflow id: {workflow_job_id}")
    return False


@call_sync
async def sync_set_slurm_job_state(workflow_job_id: str, hpc_slurm_job_state: str) -> bool:
    return await set_slurm_job_state(workflow_job_id=workflow_job_id, hpc_slurm_job_state=hpc_slurm_job_state)


async def set_workflow_job_state(job_id, job_state: str) -> bool:
    """
    set state of workflow job to 'state'
    """
    job = await get_workflow_job(job_id)
    if job:
        job.job_state = job_state
        await job.save()
        return True
    logger.warning(f"Trying to set a state to a non-existing workflow job: {job_id}")
    return False


@call_sync
async def sync_set_workflow_job_state(job_id, job_state: str) -> bool:
    return await set_workflow_job_state(job_id, job_state)


async def get_workflow_job_state(job_id) -> Union[str, None]:
    """
    get state of job
    """
    job = await get_workflow_job(job_id)
    if job:
        return job.job_state
    logger.warning(f"Trying to get a state of a non-existing workflow job: {job_id}")
    return None


@call_sync
async def sync_get_workflow_job_state(job_id) -> Union[str, None]:
    return await get_workflow_job_state(job_id)


async def get_user(email: str) -> Union[UserAccountDB, None]:
    return await UserAccountDB.find_one(UserAccountDB.email == email)


@call_sync
async def sync_get_user(email: str) -> Union[UserAccountDB, None]:
    return await get_user(email)


async def create_user(
        email: str,
        encrypted_pass: str,
        salt: str,
        account_type: str,
        approved_user: bool = False
) -> Union[UserAccountDB, None]:
    user_account = UserAccountDB(
        email=email,
        encrypted_pass=encrypted_pass,
        salt=salt,
        account_type=account_type,
        approved_user=approved_user
    )
    await user_account.save()
    return user_account


@call_sync
async def sync_create_user(
        email: str,
        encrypted_pass: str,
        salt: str,
        account_type: str,
        approved_user: bool = False
) -> Union[UserAccountDB, None]:
    return await create_user(email, encrypted_pass, salt, account_type, approved_user)
