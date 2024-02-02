import logging
from os import remove, unlink
from os.path import join
from shutil import rmtree
from typing import List, Union
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    status,
    UploadFile,
)
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils.database import db_create_workspace, db_get_workspace, db_update_workspace
from operandi_server.constants import SERVER_WORKSPACES_ROUTER, DEFAULT_METS_BASENAME
from operandi_server.exceptions import WorkspaceNotValidException
from operandi_server.files_manager import (
    create_resource_dir,
    delete_resource_dir,
    get_all_resources_url,
    get_resource_url,
    receive_resource
)
from operandi_server.models import WorkspaceRsrc
from operandi_server.utils import (
    create_workspace_bag_from_remote_url,
    extract_bag_info,
    get_ocrd_workspace_physical_pages,
    get_workspace_bag,
    validate_bag
)
from .user import user_login


router = APIRouter(tags=["Workspace"])
logger = logging.getLogger("operandi_server.routers.workspace")


@router.get("/workspace")
async def list_workspaces(auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> List[WorkspaceRsrc]:
    """
    Get a list of existing workspaces.

    Curl equivalent:
    `curl -X GET SERVER_ADDR/workspace`
    """
    await user_login(auth)
    workspaces = get_all_resources_url(SERVER_WORKSPACES_ROUTER)
    response = []
    for workspace in workspaces:
        ws_id, ws_url = workspace
        response.append(WorkspaceRsrc.create(workspace_id=ws_id, workspace_url=ws_url))
    return response


@router.get("/workspace/{workspace_id}", response_model=None)
async def get_workspace(
    background_tasks: BackgroundTasks,
    workspace_id: str,
    accept: str = Header(default="application/json"),
    auth: HTTPBasicCredentials = Depends(HTTPBasic())
) -> Union[WorkspaceRsrc, FileResponse]:
    """
    Get an existing workspace specified with `workspace_id`.
    Depending on the provided header, either a JSON response or an ocrd-zip is returned.
    By default, returns a JSON response.

    Curl equivalents:
    `curl -X GET SERVER_ADDR/workspace/{workspace_id} -H "accept: application/json"`
    `curl -X GET SERVER_ADDR/workspace/{workspace_id} -H "accept: application/vnd.ocrd+zip" -o foo.zip`
    """
    await user_login(auth)
    try:
        db_workspace = await db_get_workspace(workspace_id=workspace_id)
        workspace_url = get_resource_url(SERVER_WORKSPACES_ROUTER, resource_id=workspace_id)
    except RuntimeError:
        raise HTTPException(status_code=404, detail=f"Non-existing DB entry for workspace id:{workspace_id}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Non-existing local entry workspace id:{workspace_id}")
    if accept == "application/vnd.ocrd+zip":
        bag_path = get_workspace_bag(db_workspace)
        if not bag_path:
            raise HTTPException(status_code=404, detail=f"No bag was produced for workspace id: {workspace_id}")
        # Remove the produced bag after sending it in the response
        background_tasks.add_task(unlink, bag_path)
        return FileResponse(bag_path)
    return WorkspaceRsrc.create(workspace_id=workspace_id, workspace_url=workspace_url)


@router.post(
    path="/import_external_workspace",
    response_model=WorkspaceRsrc,
    status_code=status.HTTP_201_CREATED,
    summary="Import workspace from mets url",
    response_model_exclude_unset=True,
    response_model_exclude_none=True
)
async def post_workspace_from_url(
    mets_url: str,
    preserve_file_grps: str,
    mets_basename: str = DEFAULT_METS_BASENAME,
    auth: HTTPBasicCredentials = Depends(HTTPBasic())
) -> WorkspaceRsrc:

    await user_login(auth)
    workspace_id, workspace_dir = create_resource_dir(SERVER_WORKSPACES_ROUTER)
    bag_dest = f"{workspace_dir}.zip"

    try:
        # Split the file groups
        # E.g., `DEFAULT` -> [`DEFAULT`] ; `DEFAULT,MAX` -> ['DEFAULT', 'MAX']
        file_grps_to_preserver = preserve_file_grps.split(",")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to parse the file groups to be preserved: {error}")

    ws_dir = create_workspace_bag_from_remote_url(
        mets_url=mets_url,
        workspace_id=workspace_id,
        bag_dest=bag_dest,
        mets_basename=mets_basename,
        preserve_file_grps=file_grps_to_preserver
    )

    try:
        validate_bag(bag_dest)
    except WorkspaceNotValidException as error:
        raise HTTPException(status_code=422, detail=f"Failed to validate workspace bag: {error}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to validate workspace bag: {error}")

    # Remove old workspace dir (if any)
    rmtree(workspace_dir, ignore_errors=True)

    try:
        bag_info = extract_bag_info(bag_dest, workspace_dir)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to extract workspace bag info: {error}")
    # Remove the temporary directory
    rmtree(ws_dir, ignore_errors=True)
    # Remove the created zip bag
    remove(bag_dest)

    if "Ocrd-Mets" in bag_info:
        mets_basename = bag_info.get("Ocrd-Mets")
    try:
        physical_pages = get_ocrd_workspace_physical_pages(mets_path=join(workspace_dir, mets_basename))
        pages_amount = len(physical_pages)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to extract pages amount: {error}")

    await db_create_workspace(workspace_id, workspace_dir, pages_amount, bag_info)
    workspace_url = get_resource_url(SERVER_WORKSPACES_ROUTER, workspace_id)

    return WorkspaceRsrc.create(
        workspace_id=workspace_id,
        workspace_url=workspace_url,
        description="Workspace from Mets URL"
    )


@router.post(
    path="/workspace",
    response_model=WorkspaceRsrc,
    status_code=status.HTTP_201_CREATED,
    summary="Import workspace as an ocrd zip",
    response_model_exclude_unset=True,
    response_model_exclude_none=True
)
async def post_workspace(
    workspace: UploadFile,
    auth: HTTPBasicCredentials = Depends(HTTPBasic())
) -> WorkspaceRsrc:
    """
    Upload a new ocrd-zip workspace.
    Returns a `resource_id` with which the uploaded workspace is identified.

    Curl equivalent:
    `curl -X POST SERVER_ADDR/workspace -H "content-type: multipart/form-data" -F workspace=example_ws.ocrd.zip`
    """
    await user_login(auth)
    ws_id, ws_dir = create_resource_dir(SERVER_WORKSPACES_ROUTER, resource_id=None)
    bag_dest = f"{ws_dir}.zip"
    try:
        await receive_resource(file=workspace, resource_dst=bag_dest)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to receive the workflow resource, error: {error}")
    # Remove old workspace dir (if any)
    rmtree(ws_dir, ignore_errors=True)

    try:
        validate_bag(bag_dest)
    except WorkspaceNotValidException as error:
        raise HTTPException(status_code=422, detail=f"Failed to validate workspace bag: {error}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to validate workspace bag: {error}")

    try:
        bag_info = extract_bag_info(bag_dest, ws_dir)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to extract workspace bag info: {error}")
    remove(bag_dest)

    mets_basename = DEFAULT_METS_BASENAME
    if "Ocrd-Mets" in bag_info:
        mets_basename = bag_info.get("Ocrd-Mets")
    try:
        physical_pages = get_ocrd_workspace_physical_pages(mets_path=join(ws_dir, mets_basename))
        pages_amount = len(physical_pages)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to extract pages amount: {error}")

    await db_create_workspace(
        workspace_id=ws_id,
        workspace_dir=ws_dir,
        pages_amount=pages_amount,
        bag_info=bag_info
    )
    ws_url = get_resource_url(SERVER_WORKSPACES_ROUTER, ws_id)
    return WorkspaceRsrc.create(
        workspace_id=ws_id,
        workspace_url=ws_url,
        description="Workspace from ocrd zip"
    )


@router.put("/workspace/{workspace_id}", responses={"201": {"model": WorkspaceRsrc}})
async def put_workspace(
    workspace: UploadFile,
    workspace_id: str,
    auth: HTTPBasicCredentials = Depends(HTTPBasic())
) -> WorkspaceRsrc:
    """
    Update an existing workspace specified with `workspace_id` or create a new workspace.

    Curl equivalent:
    `curl -X PUT SERVER_ADDR/workspace/{workspace_id}
    -H "content-type: multipart/form-data" -F workspace=example_ws.ocrd.zip`
    """
    await user_login(auth)
    try:
        delete_resource_dir(SERVER_WORKSPACES_ROUTER, workspace_id)
    except FileNotFoundError:
        # Nothing to be deleted
        pass

    ws_id, ws_dir = create_resource_dir(SERVER_WORKSPACES_ROUTER, resource_id=workspace_id)
    bag_dest = f"{ws_dir}.zip"
    try:
        await receive_resource(file=workspace, resource_dst=bag_dest)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to receive the workflow resource, error: {error}")
    # Remove old workspace dir (if any)
    rmtree(ws_dir, ignore_errors=True)

    try:
        validate_bag(bag_dest)
    except WorkspaceNotValidException as error:
        raise HTTPException(status_code=422, detail=f"Failed to validate workspace bag: {error}")
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to validate workspace bag: {error}")

    try:
        bag_info = extract_bag_info(bag_dest, ws_dir)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to extract workspace bag info: {error}")
    remove(bag_dest)

    mets_basename = DEFAULT_METS_BASENAME
    if "Ocrd-Mets" in bag_info:
        mets_basename = bag_info.get("Ocrd-Mets")
    try:
        physical_pages = get_ocrd_workspace_physical_pages(mets_path=join(ws_dir, mets_basename))
        pages_amount = len(physical_pages)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to extract pages amount: {error}")

    await db_create_workspace(
        workspace_id=ws_id,
        workspace_dir=ws_dir,
        pages_amount=pages_amount,
        bag_info=bag_info
    )
    ws_url = get_resource_url(SERVER_WORKSPACES_ROUTER, ws_id)
    return WorkspaceRsrc.create(
        workspace_id=ws_id,
        workspace_url=ws_url,
        description="Workspace from ocrd zip"
    )


@router.delete("/workspace/{workspace_id}", responses={"200": {"model": WorkspaceRsrc}})
async def delete_workspace(
    workspace_id: str,
    auth: HTTPBasicCredentials = Depends(HTTPBasic())
) -> WorkspaceRsrc:
    """
    Delete an existing workspace specified with `workspace_id`

    Curl equivalent:
    `curl -X DELETE SERVER_ADDR/workspace/{workspace_id}`
    """
    await user_login(auth)
    try:
        db_workspace = await db_get_workspace(workspace_id=workspace_id)
        deleted_workspace_url = get_resource_url(SERVER_WORKSPACES_ROUTER, resource_id=workspace_id)
        delete_resource_dir(SERVER_WORKSPACES_ROUTER, workspace_id)
    except RuntimeError:
        raise HTTPException(status_code=404, detail=f"Non-existing DB entry for workspace id: {workspace_id}")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Non-existing local entry for workspace id: {workspace_id}")
    if db_workspace.deleted:
        raise HTTPException(status_code=410, detail=f"Workspace has been already deleted: {workspace_id}")
    await db_update_workspace(find_workspace_id=workspace_id, deleted=True)
    return WorkspaceRsrc.create(workspace_id=workspace_id, workspace_url=deleted_workspace_url)
