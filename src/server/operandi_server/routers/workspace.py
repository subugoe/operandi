import logging
from os import unlink
from typing import List, Union

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
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


router = APIRouter(
    tags=["Workspace"],
)

logger = logging.getLogger(__name__)
workspace_manager = WorkspaceManager()
security = HTTPBasic()


# TODO: Refine all the exceptions...
@router.get("/workspace")
async def list_workspaces(auth: HTTPBasicCredentials = Depends(security)) -> List[WorkspaceRsrc]:
    """
    Get a list of existing workspace urls

    curl http://localhost:8000/workspace/
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
        auth: HTTPBasicCredentials = Depends(security)
) -> Union[WorkspaceRsrc, FileResponse]:
    """
    Get an existing workspace

    When tested with FastAPI's interactive API docs / Swagger (e.g. http://127.0.0.1:8000/docs) the
    accept-header is always set to application/json (no matter what is specified in the gui) so to
    test getting the workspace as a zip it cannot be used.
    See: https://github.com/OCR-D/ocrd-webapi-implementation/issues/2

    can be tested with:
    `curl http://localhost:8000/workspace/-the-id-of-ws -H "accept: application/json"` and
    `curl http://localhost:8000/workspace/{ws-id} -H "accept: application/vnd.ocrd+zip" -o foo.zip`
    """
    await user_login(auth)
    try:
        workspace_url = workspace_manager.get_resource(workspace_id, local=False)
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


@router.post("/workspace", responses={"201": {"model": WorkspaceRsrc}})
async def post_workspace(
        workspace: UploadFile,
        auth: HTTPBasicCredentials = Depends(security)
) -> WorkspaceRsrc:
    """
    Create a new workspace

    curl -X POST http://localhost:8000/workspace -H 'content-type: multipart/form-data' -F workspace=@things/example_ws.ocrd.zip  # noqa
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

    return WorkspaceRsrc.create(workspace_id=ws_id, workspace_url=ws_url)


@router.put("/workspace/{workspace_id}", responses={"201": {"model": WorkspaceRsrc}})
async def put_workspace(
        workspace: UploadFile,
        workspace_id: str,
        auth: HTTPBasicCredentials = Depends(security)
) -> WorkspaceRsrc:
    """
    Update or create a workspace
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
        auth: HTTPBasicCredentials = Depends(security)
) -> WorkspaceRsrc:
    """
    Delete a workspace
    curl -v -X DELETE 'http://localhost:8000/workspace/{workspace_id}'
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
