import logging
from os import unlink
from typing import List, Union

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    status,
    UploadFile,
)
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from operandi_server.exceptions import (
    ResponseException,
    WorkspaceException,
    WorkspaceGoneException,
    WorkspaceNotValidException,
)
from operandi_server.managers import WorkspaceManager
from operandi_server.models import WorkspaceRsrc
from .user import user_login


router = APIRouter(tags=["Workspace"])

logger = logging.getLogger(__name__)
workspace_manager = WorkspaceManager()


# TODO: Refine all the exceptions...
@router.get("/workspace")
async def list_workspaces(auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> List[WorkspaceRsrc]:
    """
    Get a list of existing workspaces.

    Curl equivalent:
    `curl -X GET SERVER_ADDR/workspace`
    """
    await user_login(auth)
    workspaces = workspace_manager.get_workspaces()
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
        workspace_url = workspace_manager.get_workspace_url(workspace_id)
    except Exception as e:
        logger.exception(f"Unexpected error in get_workspace: {e}")
        # TODO: Don't provide the exception message to the outside world
        raise ResponseException(500, {"error": f"internal server error: {e}"})

    if not workspace_url:
        raise ResponseException(404, {"error": "workspace_url is None"})

    if accept == "application/vnd.ocrd+zip":
        bag_path = await workspace_manager.get_workspace_bag(workspace_id)
        if not bag_path:
            raise ResponseException(404, {"error": "bag_path is None"})
        # Remove the produced bag after sending it in the response
        background_tasks.add_task(unlink, bag_path)
        return FileResponse(bag_path)

    return WorkspaceRsrc.create(workspace_id=workspace_id, workspace_url=workspace_url)


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
    try:
        ws_url, ws_id = await workspace_manager.create_workspace_from_zip(workspace)
    except WorkspaceNotValidException as e:
        raise ResponseException(422, {"error": "workspace not valid", "reason": str(e)})
    except Exception as e:
        logger.exception(f"Unexpected error in post_workspace: {e}")
        # TODO: Don't provide the exception message to the outside world
        raise ResponseException(500, {"error": f"internal server error: {e}"})

    return WorkspaceRsrc.create(
        workspace_id=ws_id,
        workspace_url=ws_url,
        description="Workspace from ocrd zip"
    )


@router.post(
    path="/workspace/import_external",
    response_model=WorkspaceRsrc,
    status_code=status.HTTP_201_CREATED,
    summary="Import workspace from mets url",
    response_model_exclude_unset=True,
    response_model_exclude_none=True
)
async def post_workspace_from_url(
        mets_url: str,
        file_grp: str = "DEFAULT",
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
) -> WorkspaceRsrc:

    await user_login(auth)
    try:
        ws_url, ws_id = await workspace_manager.create_workspace_from_mets_url(
            mets_url=mets_url,
            file_grp=file_grp,
            mets_basename="mets.xml"
        )
    except WorkspaceNotValidException as e:
        raise ResponseException(422, {"error": "workspace not valid", "reason": str(e)})
    except Exception as e:
        logger.exception(f"Unexpected error in create_workspace_from_zip: {e}")
        # TODO: Don't provide the exception message to the outside world
        raise ResponseException(500, {"error": f"internal server error: {e}"})

    return WorkspaceRsrc.create(
        workspace_id=ws_id,
        workspace_url=ws_url,
        description="Workspace from Mets URL"
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
    `curl -X PUT SERVER_ADDR/workspace/{workspace_id} -H "content-type: multipart/form-data" -F workspace=example_ws.ocrd.zip`
    """
    await user_login(auth)
    try:
        updated_workspace_url = await workspace_manager.update_workspace(file=workspace, workspace_id=workspace_id)
    except WorkspaceNotValidException as e:
        raise ResponseException(422, {"error": "workspace not valid", "reason": str(e)})
    except Exception as e:
        logger.exception(f"Unexpected error in put_workspace: {e}")
        # TODO: Don't provide the exception message to the outside world
        raise ResponseException(500, {"error": f"internal server error: {e}"})

    return WorkspaceRsrc.create(workspace_id=workspace_id, workspace_url=updated_workspace_url)


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
        deleted_workspace_url = await workspace_manager.delete_workspace(
            workspace_id
        )
    except WorkspaceGoneException as e:
        raise ResponseException(410, {"error:": f"{e}"})
    except WorkspaceException as e:
        raise ResponseException(404, {"error:": f"{e}"})
    except Exception as e:
        logger.exception(f"Unexpected error in delete_workspace: {e}")
        # TODO: Don't provide the exception message to the outside world
        raise ResponseException(500, {"error": f"internal server error: {e}"})

    return WorkspaceRsrc.create(workspace_id=workspace_id, workspace_url=deleted_workspace_url)
