from typing import List
from datetime import datetime
from os.path import join
from operandi_utils import call_sync
from operandi_utils.constants import StateWorkspace
from .models import DBWorkspace


# TODO: This also updates to satisfy the PUT method in the Workspace Manager - fix this
async def db_create_workspace(
    user_id: str, workspace_id: str, workspace_dir: str, pages_amount: int, file_groups: List[str], bag_info: dict,
    state: StateWorkspace = StateWorkspace.UNSET, default_mets_basename: str = "mets.xml",
    details: str = "Workspace"
) -> DBWorkspace:
    bag_info = dict(bag_info)
    mets_basename = default_mets_basename
    workspace_mets_path = join(workspace_dir, mets_basename)
    ocrd_base_version_checksum = None
    ocrd_identifier = bag_info.pop("Ocrd-Identifier")
    bagit_profile_identifier = bag_info.pop("BagIt-Profile-Identifier")
    if "Ocrd-Mets" in bag_info:
        mets_basename = bag_info.pop("Ocrd-Mets")
        workspace_mets_path = join(workspace_dir, mets_basename)  # Replace it with the real path
    if "Ocrd-Base-Version-Checksum" in bag_info:
        ocrd_base_version_checksum = bag_info.pop("Ocrd-Base-Version-Checksum")

    try:
        db_workspace = await db_get_workspace(workspace_id)
    except RuntimeError:
        db_workspace = DBWorkspace(
            user_id=user_id,
            workspace_id=workspace_id,
            workspace_dir=workspace_dir,
            workspace_mets_path=workspace_mets_path,
            pages_amount=pages_amount,
            file_groups=file_groups,
            state=state,
            mets_basename=mets_basename,
            ocrd_identifier=ocrd_identifier,
            bagit_profile_identifier=bagit_profile_identifier,
            ocrd_base_version_checksum=ocrd_base_version_checksum,
            bag_info_adds=bag_info,
            datetime=datetime.now(),
            details=details
        )
    else:
        db_workspace.user_id = user_id
        db_workspace.workspace_dir = workspace_dir
        db_workspace.workspace_mets_path = workspace_mets_path
        db_workspace.mets_basename = mets_basename
        db_workspace.pages_amount = pages_amount
        db_workspace.file_groups = file_groups
        db_workspace.ocrd_identifier = ocrd_identifier
        db_workspace.bagit_profile_identifier = bagit_profile_identifier
        db_workspace.ocrd_base_version_checksum = ocrd_base_version_checksum
        db_workspace.bag_info_adds = bag_info
        db_workspace.details = details
    await db_workspace.save()
    return db_workspace


@call_sync
async def sync_db_create_workspace(
    user_id: str, workspace_id: str, workspace_dir: str, pages_amount: int, file_groups: List[str], bag_info: dict,
    state: StateWorkspace = StateWorkspace.UNSET, details: str = "Workspace"
) -> DBWorkspace:
    return await db_create_workspace(
        user_id, workspace_id, workspace_dir, pages_amount, file_groups, bag_info, state, details)


async def db_get_workspace(workspace_id: str) -> DBWorkspace:
    db_workspace = await DBWorkspace.find_one(DBWorkspace.workspace_id == workspace_id)
    if not db_workspace:
        raise RuntimeError(f"No DB workspace entry found for id: {workspace_id}")
    return db_workspace


@call_sync
async def sync_db_get_workspace(workspace_id: str) -> DBWorkspace:
    return await db_get_workspace(workspace_id)


async def db_update_workspace(find_workspace_id: str, **kwargs) -> DBWorkspace:
    db_workspace = await db_get_workspace(workspace_id=find_workspace_id)
    model_keys = list(db_workspace.__dict__.keys())
    for key, value in kwargs.items():
        if key not in model_keys:
            raise ValueError(f"Field not available: {key}")
        if key == "workspace_id":
            db_workspace.workspace_id = value
        elif key == "workspace_dir":
            db_workspace.workspace_dir = value
        elif key == "workspace_mets_path":
            db_workspace.workspace_mets_path = value
        elif key == "pages_amount":
            db_workspace.pages_amount = value
        elif key == "file_groups":
            db_workspace.file_groups = value
        elif key == "state":
            db_workspace.state = value
        elif key == "ocrd_identifier":
            db_workspace.ocrd_identifier = value
        elif key == "bagit_profile_identifier":
            db_workspace.bagit_profile_identifier = value
        elif key == "ocrd_base_version_checksum":
            db_workspace.ocrd_base_version_checksum = value
        elif key == "mets_basename":
            db_workspace.ocrd_mets = value
        elif key == "bag_info_adds":
            db_workspace.bag_info_adds = value
        elif key == "deleted":
            db_workspace.deleted = value
        elif key == "details":
            db_workspace.details = value
        else:
            raise ValueError(f"Field not updatable: {key}")
    await db_workspace.save()
    return db_workspace


@call_sync
async def sync_db_update_workspace(find_workspace_id: str, **kwargs) -> DBWorkspace:
    return await db_update_workspace(find_workspace_id=find_workspace_id, **kwargs)
