from logging import getLogger
from os import unlink
from os.path import join
from pathlib import Path
from shutil import rmtree
from typing import List, Union
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
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
from .user import RouterUser


class RouterWorkspace:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.workspace")
        self.user_authenticator = RouterUser()
        self.router = APIRouter(tags=["Workspace"])
        self.router.add_api_route(
            path="/workspace",
            endpoint=self.list_workspaces,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            summary="Get a list of existing workspaces.",
            response_model=List[WorkspaceRsrc],
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workspace/{workspace_id}",
            endpoint=self.download_workspace,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            summary="Get a list of existing workspaces.",
            response_model=None,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/import_external_workspace",
            endpoint=self.upload_workspace_from_url,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            summary="""
            Import workspace from mets url.
            Returns a `resource_id` associated with the uploaded workspace.
            """,
            response_model=WorkspaceRsrc,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workspace",
            endpoint=self.upload_workspace,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            summary="""
            Import workspace as an ocrd zip.
            Returns a `resource_id` associated with the uploaded workspace.
            """,
            response_model=WorkspaceRsrc,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workspace/{workspace_id}",
            endpoint=self.upload_workspace,
            methods=["PUT"],
            status_code=status.HTTP_201_CREATED,
            summary="""
            Update an existing workspace specified with `workspace_id` or create a new workspace.
            """,
            response_model=WorkspaceRsrc,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workspace/{workspace_id}",
            endpoint=self.delete_workspace,
            methods=["DELETE"],
            status_code=status.HTTP_200_OK,
            summary="""
            Delete an existing workspace identified with `workspace_id`.
            """,
            response_model=WorkspaceRsrc,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )

    def _validate_bag_with_error_handling(self, bag_dst: str) -> None:
        message = "Failed to validate workspace bag"
        try:
            validate_bag(bag_dst)
        except WorkspaceNotValidException as error:
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)
        except Exception as error:
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

    def _extract_bag_info_with_error_handling(self, bag_dst: str, ws_dir: str) -> dict:
        try:
            bag_info = extract_bag_info(bag_dst, ws_dir)
        except Exception as error:
            message = "Failed to extract workspace bag info"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)
        return bag_info

    def _extract_pages_with_error_handling(self, bag_info: dict, ws_dir: str) -> int:
        mets_basename = DEFAULT_METS_BASENAME
        if "Ocrd-Mets" in bag_info:
            mets_basename = bag_info.get("Ocrd-Mets")
        try:
            physical_pages = get_ocrd_workspace_physical_pages(mets_path=join(ws_dir, mets_basename))
            pages_amount = len(physical_pages)
        except Exception as error:
            message = "Failed to extract pages amount"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
        return pages_amount

    async def list_workspaces(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> List[WorkspaceRsrc]:
        """
        Curl equivalent:
        `curl -X GET SERVER_ADDR/workspace`
        """
        await self.user_authenticator.user_login(auth)
        workspaces = get_all_resources_url(SERVER_WORKSPACES_ROUTER)
        response = []
        for workspace in workspaces:
            ws_id, ws_url = workspace
            response.append(WorkspaceRsrc.create(workspace_id=ws_id, workspace_url=ws_url))
        return response

    async def download_workspace(
        self,
        background_tasks: BackgroundTasks,
        workspace_id: str,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> Union[WorkspaceRsrc, FileResponse]:
        """
        Curl equivalent:
        `curl -X GET SERVER_ADDR/workspace/{workspace_id} -H "accept: application/vnd.ocrd+zip" -o foo.zip`
        """
        await self.user_authenticator.user_login(auth)
        try:
            db_workspace = await db_get_workspace(workspace_id=workspace_id)
        except RuntimeError as error:
            message = f"Non-existing DB entry for workspace id:{workspace_id}"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        except FileNotFoundError as error:
            message = f"Non-existing local entry workspace id:{workspace_id}"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

        message = f"No bag was produced for workspace id: {workspace_id}"
        try:
            bag_path = get_workspace_bag(db_workspace)
            if not bag_path:
                self.logger.error(message)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        except Exception as error:
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        background_tasks.add_task(unlink, bag_path)
        return FileResponse(bag_path)

    async def upload_workspace_from_url(
        self,
        mets_url: str,
        preserve_file_grps: str,
        mets_basename: str = DEFAULT_METS_BASENAME,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkspaceRsrc:
        await self.user_authenticator.user_login(auth)
        workspace_id, workspace_dir = create_resource_dir(SERVER_WORKSPACES_ROUTER)
        bag_dest = f"{workspace_dir}.zip"
        try:
            # Split the file groups
            # E.g., `DEFAULT` -> [`DEFAULT`] ; `DEFAULT,MAX` -> ['DEFAULT', 'MAX']
            file_grps_to_preserver = preserve_file_grps.split(",")
        except Exception as error:
            message = "Failed to parse the file groups to be preserved"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)

        try:
            ws_temp_dir = create_workspace_bag_from_remote_url(
                mets_url=mets_url,
                workspace_id=workspace_id,
                bag_dest=bag_dest,
                mets_basename=mets_basename,
                preserve_file_grps=file_grps_to_preserver
            )
        except Exception as error:
            message = "Failed to create workspace bag from remote url"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)

        rmtree(ws_temp_dir, ignore_errors=True)  # Remove the temp dir
        rmtree(workspace_dir, ignore_errors=True)  # Remove old workspace dir (if any)
        self._validate_bag_with_error_handling(bag_dst=bag_dest)
        bag_info = self._extract_bag_info_with_error_handling(bag_dst=bag_dest, ws_dir=workspace_dir)
        Path(bag_dest).unlink()  # Remove the created zip bag
        pages_amount = self._extract_pages_with_error_handling(bag_info, workspace_dir)
        await db_create_workspace(
            workspace_id=workspace_id,
            workspace_dir=workspace_dir,
            pages_amount=pages_amount,
            bag_info=bag_info
        )
        workspace_url = get_resource_url(SERVER_WORKSPACES_ROUTER, workspace_id)
        return WorkspaceRsrc.create(
            workspace_id=workspace_id,
            workspace_url=workspace_url,
            description="Workspace from Mets URL"
        )

    async def upload_workspace(
        self,
        workspace: UploadFile,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkspaceRsrc:
        """
        Curl equivalent:
        `curl -X POST SERVER_ADDR/workspace -H "content-type: multipart/form-data" -F workspace=example_ws.ocrd.zip`
        """
        await self.user_authenticator.user_login(auth)
        ws_id, ws_dir = create_resource_dir(SERVER_WORKSPACES_ROUTER, resource_id=None)
        bag_dest = f"{ws_dir}.zip"
        try:
            await receive_resource(file=workspace, resource_dst=bag_dest)
        except Exception as error:
            message = "Failed to receive the workspace resource"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        rmtree(ws_dir, ignore_errors=True)  # Remove old workspace dir (if any)
        self._validate_bag_with_error_handling(bag_dst=bag_dest)
        bag_info = self._extract_bag_info_with_error_handling(bag_dst=bag_dest, ws_dir=ws_dir)
        Path(bag_dest).unlink()  # Remove the created zip bag
        pages_amount = self._extract_pages_with_error_handling(bag_info, ws_dir)
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

    async def put_workspace(
        self,
        workspace: UploadFile,
        workspace_id: str,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkspaceRsrc:
        """
        Curl equivalent:
        `curl -X PUT SERVER_ADDR/workspace/{workspace_id}
        -H "content-type: multipart/form-data" -F workspace=example_ws.ocrd.zip`
        """
        await self.user_authenticator.user_login(auth)
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
            message = "Failed to receive the workspace resource"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        rmtree(ws_dir, ignore_errors=True)  # Remove old workspace dir (if any)
        self._validate_bag_with_error_handling(bag_dst=bag_dest)
        bag_info = self._extract_bag_info_with_error_handling(bag_dst=bag_dest, ws_dir=ws_dir)
        Path(bag_dest).unlink()
        pages_amount = self._extract_pages_with_error_handling(bag_info, ws_dir)
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

    async def delete_workspace(
        self,
        workspace_id: str,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkspaceRsrc:
        """
        Curl equivalent:
        `curl -X DELETE SERVER_ADDR/workspace/{workspace_id}`
        """
        await self.user_authenticator.user_login(auth)
        try:
            db_workspace = await db_get_workspace(workspace_id=workspace_id)
            deleted_workspace_url = get_resource_url(SERVER_WORKSPACES_ROUTER, resource_id=workspace_id)
            delete_resource_dir(SERVER_WORKSPACES_ROUTER, workspace_id)
        except RuntimeError as error:
            message = f"Non-existing DB entry for workspace_id: {workspace_id}"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        except FileNotFoundError as error:
            message = f"Non-existing local entry workspace_id: {workspace_id}"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        if db_workspace.deleted:
            message = f"Workspace has been already deleted: {workspace_id}"
            self.logger.warning(f"{message}")
            raise HTTPException(status_code=status.HTTP_410_GONE, detail=message)
        await db_update_workspace(find_workspace_id=workspace_id, deleted=True)
        return WorkspaceRsrc.create(workspace_id=workspace_id, workspace_url=deleted_workspace_url)
