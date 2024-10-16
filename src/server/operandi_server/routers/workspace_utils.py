import bagit
from fastapi import HTTPException, status
from os.path import join
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Union
from zipfile import ZipFile

from ocrd import Resolver
from ocrd.workspace import Workspace
from ocrd.workspace_bagger import WorkspaceBagger
from ocrd_validators.ocrd_zip_validator import OcrdZipValidator

from operandi_server.constants import DEFAULT_FILE_GRP, DEFAULT_METS_BASENAME
from operandi_server.exceptions import WorkspaceNotValidException
from operandi_utils.constants import StateWorkspace
from operandi_utils.database import db_get_workspace
from operandi_utils.database.models import DBWorkspace


def get_ocrd_workspace_physical_pages(mets_path: str) -> List[str]:
    return Resolver().workspace_from_url(mets_url=mets_path).mets.physical_pages

def extract_pages_with_handling(logger, bag_info: dict, ws_dir: str) -> int:
    mets_basename = DEFAULT_METS_BASENAME
    if "Ocrd-Mets" in bag_info:
        mets_basename = bag_info.get("Ocrd-Mets")
    try:
        physical_pages = get_ocrd_workspace_physical_pages(mets_path=join(ws_dir, mets_basename))
        pages_amount = len(physical_pages)
    except Exception as error:
        message = "Failed to extract pages amount"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
    return pages_amount

def get_ocrd_workspace_file_groups(mets_path: str) -> List[str]:
    return Resolver().workspace_from_url(mets_url=mets_path).mets.file_groups

def extract_file_groups_with_handling(logger, bag_info: dict, ws_dir: str) -> List[str]:
    mets_basename = DEFAULT_METS_BASENAME
    if "Ocrd-Mets" in bag_info:
        mets_basename = bag_info.get("Ocrd-Mets")
    try:
        file_groups = get_ocrd_workspace_file_groups(mets_path=join(ws_dir, mets_basename))
    except Exception as error:
        message = "Failed to extract file groups"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
    return file_groups


def create_workspace_bag(db_workspace) -> Union[str, None]:
    """
    Create workspace bag.

    The resulting zip is stored in the workspaces' directory (`self._resource_dir`).
    The Workspace could have been changed so recreation of bag-files is necessary.
    Simply zipping is not sufficient.

    Args:
         db_workspace (DBWorkspace): database model of the workspace
    Returns:
        path to created bag
    """
    bag_dest = f"{db_workspace.workspace_dir}.zip"
    mets_basename = db_workspace.mets_basename
    if not mets_basename:
        mets_basename = DEFAULT_METS_BASENAME
    resolver = Resolver()
    workspace = Workspace(resolver, directory=db_workspace.workspace_dir, mets_basename=mets_basename)
    # Warning: do not set processes to a higher value than 1, it would crash the Uvicorn internals
    WorkspaceBagger(resolver).bag(
        workspace, ocrd_identifier=db_workspace.ocrd_identifier, dest=bag_dest, ocrd_mets=mets_basename, processes=1)
    return bag_dest


def create_workspace_bag_from_remote_url(
    mets_url: str, workspace_id: str, bag_dest: str, mets_basename: str = DEFAULT_METS_BASENAME,
    preserve_file_grps: List[str] = None
) -> str:
    if not preserve_file_grps:
        preserve_file_grps = [DEFAULT_FILE_GRP]
    resolver = Resolver()
    # Create an OCR-D Workspace from a remote mets URL
    # without downloading the files referenced in the mets file
    workspace = resolver.workspace_from_url(
        mets_url=mets_url, clobber_mets=False, mets_basename=mets_basename, download=False)

    remove_groups = [x for x in workspace.mets.file_groups if x not in preserve_file_grps]
    for group in remove_groups:
        workspace.remove_file_group(group, recursive=True, force=True)
    workspace.save_mets()
    ws_files = workspace.find_files()
    for ws_file in ws_files:
        workspace.download_file(f=ws_file)

    # Resolves and downloads all file groups and files in the mets file
    # Warning: do not set processes to a higher value than 1, it would crash the Uvicorn internals
    WorkspaceBagger(resolver).bag(workspace, dest=bag_dest, ocrd_identifier=workspace_id, processes=1)
    return workspace.directory


def extract_bag_info(bag_dest, workspace_dir) -> dict:
    workspace_bagger = WorkspaceBagger(Resolver())
    workspace_bagger.spill(bag_dest, workspace_dir)

    # TODO: work is done twice here: spill already extracts the bag-info.txt but throws it away.
    #  maybe workspace_bagger.spill can be changed to deliver the bag-info.txt here
    with ZipFile(bag_dest, mode='r') as zip_fp:
        bag_info_bytes = zip_fp.read("bag-info.txt")
        with NamedTemporaryFile() as tmp_file:
            with open(tmp_file.name, mode="wb") as f:
                f.write(bag_info_bytes)
            bag_info = bagit._load_tag_file(tmp_file.name)
    return bag_info


def extract_bag_info_with_handling(logger, bag_dst: str, ws_dir: str) -> dict:
    try:
        bag_info = extract_bag_info(bag_dst, ws_dir)
    except Exception as error:
        message = "Failed to extract workspace bag info"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)
    return bag_info


def validate_bag(bag_dest: str):
    try:
        # Warning: do not set processes to a higher value than 1, it would crash the Uvicorn internals
        valid_report = OcrdZipValidator(Resolver(), bag_dest).validate(processes=1)
    except Exception as e:
        raise WorkspaceNotValidException(f"Error during workspace validation: {str(e)}") from e
    if valid_report and not valid_report.is_valid:
        raise WorkspaceNotValidException(valid_report.to_xml())


def validate_bag_with_handling(logger, bag_dst: str) -> None:
    message = "Failed to validate workspace bag"
    try:
        validate_bag(bag_dst)
    except WorkspaceNotValidException as error:
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)
    except Exception as error:
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)


async def get_db_workspace_with_handling(
    logger, workspace_id: str, check_ready: bool = True, check_deleted: bool = True, check_local_existence: bool = True
) -> DBWorkspace:
    try:
        db_workspace = await db_get_workspace(workspace_id=workspace_id)
    except RuntimeError as error:
        message = f"Non-existing DB entry for workspace id: {workspace_id}"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    if check_deleted and db_workspace.deleted:
        message = f"Workspace has been deleted: {workspace_id}"
        logger.error(f"{message}")
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=message)
    if check_local_existence and not Path(db_workspace.workspace_mets_path).exists:
        message = f"Non-existing local entry workspace id: {workspace_id}"
        logger.error(f"{message}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    if check_ready and db_workspace.state != StateWorkspace.READY:
        message = f"The workspace is not ready yet, current state: {db_workspace.state}"
        logger.error(f"{message}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
    return db_workspace


def parse_file_groups_with_handling(logger, file_groups: str) -> List[str]:
    try:
        file_groups = file_groups.split(",")
    except Exception as error:
        message = "Failed to parse the file groups parameter"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)
    return file_groups


def remove_file_groups_with_handling(
    logger, db_workspace, file_groups: List[str], recursive: bool = True, force: bool = True
) -> List[str]:
    try:
        resolver = Resolver()
        # Create an OCR-D Workspace from a remote mets URL
        # without downloading the files referenced in the mets file
        workspace = resolver.workspace_from_url(
            mets_url=db_workspace.workspace_mets_path, clobber_mets=False, mets_basename=db_workspace.mets_basename,
            download=False)
        for file_group in file_groups:
            workspace.remove_file_group(file_group, recursive=recursive, force=force)
        workspace.save_mets()
        return workspace.mets.file_groups
    except Exception as error:
        message = "Failed to parse the file groups to be removed"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

def extract_file_groups_from_db_model_with_handling(logger, db_workspace) -> List[str]:
    try:
        resolver = Resolver()
        workspace = resolver.workspace_from_url(
            mets_url=db_workspace.workspace_mets_path, clobber_mets=False, mets_basename=db_workspace.mets_basename,
            download=False)
        return workspace.mets.file_groups
    except Exception as error:
        message = f"Failed to extract file groups for: {db_workspace.workspace_id}"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

def check_if_file_group_exists_with_handling(logger, db_workspace, file_group: str) -> bool:
    file_groups = extract_file_groups_from_db_model_with_handling(logger, db_workspace)
    return file_group in file_groups
