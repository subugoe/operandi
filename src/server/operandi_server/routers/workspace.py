from logging import getLogger
from os import unlink
from pathlib import Path
from shutil import rmtree
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils.constants import ServerApiTag, StateWorkspace
from operandi_utils.database import (
    db_create_workspace, db_get_workspace, db_update_workspace, db_increase_processing_stats_with_handling)
from operandi_server.constants import DEFAULT_METS_BASENAME
from operandi_server.files_manager import receive_resource
from operandi_server.files_manager import LFMInstance
from operandi_server.models import MetsUrlRequest, WorkspaceRsrc
from .workspace_utils import (
    create_workspace_bag,
    create_workspace_bag_from_remote_url,
    extract_bag_info_with_handling,
    extract_file_groups_with_handling,
    extract_pages_with_handling,
    validate_bag_with_handling,
    get_db_workspace_with_handling,
    parse_file_groups_with_handling,
    remove_file_groups_with_handling
)
from .user_utils import user_auth_with_handling

class RouterWorkspace:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.workspace")
        self.router = APIRouter(tags=[ServerApiTag.WORKSPACE])
        self.router.add_api_route(
            path="/import_external_workspace",
            endpoint=self.upload_workspace_from_url, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="Import workspace from mets url. Returns a `resource_id` associated with the uploaded workspace.",
            response_model=WorkspaceRsrc, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workspace",
            endpoint=self.upload_workspace, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="Import workspace as an ocrd zip. Returns a `resource_id` associated with the uploaded workspace.",
            response_model=WorkspaceRsrc, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/batch-workspaces",
            endpoint=self.upload_batch_workspaces, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="Upload a list of workspaces each as an ocrd zip (limit:5). "
                    "Returns a list of `resource_id`s associated with the uploaded workspaces.",
            response_model=List[WorkspaceRsrc], response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/batch-workspaces-urls",
            endpoint=self.upload_batch_workspaces_from_urls, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="Upload a list of workspaces each as a URL referencing a mets file (limit:5). "
                    "Returns a list of `resource_id`s associated with the uploaded workspaces.",
            response_model=List[WorkspaceRsrc], response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workspace/{workspace_id}",
            endpoint=self.download_workspace, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Download an existing workspace zip identified with `workspace_id`.",
            response_model=None, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workspace/{workspace_id}",
            endpoint=self.upload_workspace, methods=["PUT"], status_code=status.HTTP_201_CREATED,
            summary="Update an existing workspace specified with `workspace_id` or create a new workspace.",
            response_model=WorkspaceRsrc, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/workspace/{workspace_id}",
            endpoint=self.delete_workspace, methods=["DELETE"], status_code=status.HTTP_200_OK,
            summary="Delete an existing workspace identified with `workspace_id`.",
            response_model=WorkspaceRsrc, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/remove_file_group/{workspace_id}",
            endpoint=self.remove_file_group_from_workspace, methods=["DELETE"], status_code=status.HTTP_201_CREATED,
            summary="Remove file groups from a workspace",
            response_model=WorkspaceRsrc, response_model_exclude_unset=True, response_model_exclude_none=True
        )

    async def download_workspace(
        self, background_tasks: BackgroundTasks, workspace_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> FileResponse:
        """
        Curl equivalent:
        `curl -X GET SERVER_ADDR/workspace/{workspace_id} -H "accept: application/vnd.ocrd+zip" -o foo.zip`
        """
        py_user_action = await user_auth_with_handling(self.logger, auth)
        db_workspace = await get_db_workspace_with_handling(
            self.logger, workspace_id, check_ready=True, check_deleted=True, check_local_existence=True)

        message = f"No bag was produced for workspace id: {workspace_id}"
        try:
            bag_path = create_workspace_bag(db_workspace)
            if not bag_path:
                self.logger.error(message)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        except Exception as error:
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

        await db_increase_processing_stats_with_handling(
            self.logger, find_user_id=py_user_action.user_id, pages_downloaded=db_workspace.pages_amount)

        background_tasks.add_task(unlink, bag_path)
        return FileResponse(path=bag_path, filename=f"{workspace_id}.ocrd.zip", media_type="application/ocrd+zip")

    async def upload_workspace_from_url(
        self, mets_url: str, preserve_file_grps: str, mets_basename: str = DEFAULT_METS_BASENAME,
        details: str = f"Workspace imported from a mets file url", auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkspaceRsrc:
        py_user_action = await user_auth_with_handling(self.logger, auth)
        file_grps_to_preserve = parse_file_groups_with_handling(self.logger, file_groups=preserve_file_grps)
        workspace_id, workspace_dir = LFMInstance.make_dir_workspace()
        bag_dest = f"{workspace_dir}.zip"
        try:
            ws_temp_dir = create_workspace_bag_from_remote_url(
                mets_url=mets_url, workspace_id=workspace_id, bag_dest=bag_dest, mets_basename=mets_basename,
                preserve_file_grps=file_grps_to_preserve)
        except Exception as error:
            message = "Failed to create workspace bag from remote url"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message)

        rmtree(ws_temp_dir, ignore_errors=True)  # Remove the temp dir
        rmtree(workspace_dir, ignore_errors=True)  # Remove old workspace dir (if any)
        validate_bag_with_handling(self.logger, bag_dst=bag_dest)
        bag_info = extract_bag_info_with_handling(self.logger, bag_dst=bag_dest, ws_dir=workspace_dir)
        Path(bag_dest).unlink()  # Remove the created zip bag
        pages_amount = extract_pages_with_handling(self.logger, bag_info, workspace_dir)
        file_groups = extract_file_groups_with_handling(self.logger, bag_info, workspace_dir)

        user_id = py_user_action.user_id
        db_workspace = await db_create_workspace(
            user_id=user_id, workspace_id=workspace_id, workspace_dir=workspace_dir, pages_amount=pages_amount,
            file_groups=file_groups, bag_info=bag_info, state=StateWorkspace.READY, details=details)
        await db_increase_processing_stats_with_handling(self.logger, find_user_id=user_id, pages_uploaded=pages_amount)
        return WorkspaceRsrc.from_db_workspace(db_workspace)

    async def upload_workspace(
        self, workspace: UploadFile, details: str = f"Workspace uploaded as an OCRD zip format",
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkspaceRsrc:
        """
        Curl equivalent:
        `curl -X POST SERVER_ADDR/workspace -H "content-type: multipart/form-data" -F workspace=example_ws.ocrd.zip`
        """
        py_user_action = await user_auth_with_handling(self.logger, auth)
        ws_id, ws_dir = LFMInstance.make_dir_workspace()
        bag_dest = f"{ws_dir}.zip"
        try:
            await receive_resource(file=workspace, resource_dst=bag_dest)
        except Exception as error:
            message = "Failed to receive the workspace resource"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        rmtree(ws_dir, ignore_errors=True)  # Remove old workspace dir (if any)
        validate_bag_with_handling(self.logger, bag_dst=bag_dest)
        bag_info = extract_bag_info_with_handling(self.logger, bag_dst=bag_dest, ws_dir=ws_dir)
        Path(bag_dest).unlink()  # Remove the created zip bag
        pages_amount = extract_pages_with_handling(self.logger, bag_info, ws_dir)
        file_groups = extract_file_groups_with_handling(self.logger, bag_info, ws_dir)

        user_id = py_user_action.user_id
        db_workspace = await db_create_workspace(
            user_id=user_id, workspace_id=ws_id, workspace_dir=ws_dir, pages_amount=pages_amount,
            file_groups=file_groups, bag_info=bag_info, state=StateWorkspace.READY, details=details)
        await db_increase_processing_stats_with_handling(self.logger, find_user_id=user_id, pages_uploaded=pages_amount)
        return WorkspaceRsrc.from_db_workspace(db_workspace)

    async def put_workspace(
        self, workspace: UploadFile, workspace_id: str, details: str = f"Workspace uploaded as an OCRD zip format",
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkspaceRsrc:
        """
        Curl equivalent:
        `curl -X PUT SERVER_ADDR/workspace/{workspace_id}
        -H "content-type: multipart/form-data" -F workspace=example_ws.ocrd.zip`
        """
        py_user_action = await user_auth_with_handling(self.logger, auth)
        try:
            await db_get_workspace(workspace_id=workspace_id)
            # Note: This check raises HTTP errors on RuntimeError for
            # missing database entries, hence, the additional check above is a must
            await get_db_workspace_with_handling(
                self.logger, workspace_id, check_ready=True, check_deleted=False, check_local_existence=False)
        except RuntimeError:
            # Non-existing DB entry, ignore since that case is acceptable for PUT
            pass

        LFMInstance.delete_dir_workspace(workspace_id=workspace_id, missing_ok=True)
        ws_id, ws_dir = LFMInstance.make_dir_workspace(workspace_id=workspace_id)
        bag_dest = f"{ws_dir}.zip"
        try:
            await receive_resource(file=workspace, resource_dst=bag_dest)
        except Exception as error:
            message = "Failed to receive the workspace resource"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        rmtree(ws_dir, ignore_errors=True)  # Remove old workspace dir (if any)
        validate_bag_with_handling(self.logger, bag_dst=bag_dest)
        bag_info = extract_bag_info_with_handling(self.logger, bag_dst=bag_dest, ws_dir=ws_dir)
        Path(bag_dest).unlink()
        pages_amount = extract_pages_with_handling(self.logger, bag_info, ws_dir)
        file_groups = extract_file_groups_with_handling(self.logger, bag_info, ws_dir)

        user_id = py_user_action.user_id
        db_workspace = await db_create_workspace(
            user_id=user_id, workspace_id=ws_id, workspace_dir=ws_dir, pages_amount=pages_amount,
            file_groups=file_groups, bag_info=bag_info, state=StateWorkspace.READY, details=details)
        await db_increase_processing_stats_with_handling(self.logger, find_user_id=user_id, pages_uploaded=pages_amount)
        return WorkspaceRsrc.from_db_workspace(db_workspace)

    async def delete_workspace(
        self, workspace_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkspaceRsrc:
        """
        Curl equivalent:
        `curl -X DELETE SERVER_ADDR/workspace/{workspace_id}`
        """
        await user_auth_with_handling(self.logger, auth)
        await get_db_workspace_with_handling(
            self.logger, workspace_id, check_ready=True, check_deleted=True, check_local_existence=True)

        db_workspace = await db_update_workspace(find_workspace_id=workspace_id, deleted=True)
        workspace_rsrc = WorkspaceRsrc.from_db_workspace(db_workspace)
        try:
            LFMInstance.delete_dir_workspace(workspace_id=workspace_id, missing_ok=False)
        except FileNotFoundError as error:
            message = f"Non-existing local entry workspace_id: {workspace_id}"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        return workspace_rsrc

    async def remove_file_group_from_workspace(
        self, workspace_id: str, remove_file_grps: str, recursive: bool = True, force: bool = True,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> WorkspaceRsrc:
        await user_auth_with_handling(self.logger, auth)
        db_workspace = await get_db_workspace_with_handling(
            self.logger, workspace_id, check_ready=True, check_deleted=True, check_local_existence=True
        )
        file_grps_to_remove = parse_file_groups_with_handling(self.logger, file_groups=remove_file_grps)
        remaining_file_groups = remove_file_groups_with_handling(
            self.logger, db_workspace=db_workspace, file_groups=file_grps_to_remove, recursive=recursive, force=force
        )
        db_workspace = await db_update_workspace(find_workspace_id=workspace_id, file_groups=remaining_file_groups)
        return WorkspaceRsrc.from_db_workspace(db_workspace)

    async def upload_batch_workspaces(
        self, workspaces: List[UploadFile], auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> List[WorkspaceRsrc]:
        """
        Curl equivalent:
        `curl -X POST SERVER_ADDR/batch-workspaces -F files=@workspace1.zip -F files=@workspace2.zip ...`
        """
        py_user_action = await user_auth_with_handling(self.logger, auth)
        if len(workspaces) > 5:
            message = "Batch upload exceeds the limit of 5 workspaces"
            self.logger.error(message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        workspace_resources = []
        for workspace in workspaces:
            ws_id, ws_dir = LFMInstance.make_dir_workspace()
            bag_dest = f"{ws_dir}.zip"
            try:
                await receive_resource(file=workspace, resource_dst=bag_dest)
                rmtree(ws_dir, ignore_errors=True)
                validate_bag_with_handling(self.logger, bag_dst=bag_dest)
                bag_info = extract_bag_info_with_handling(self.logger, bag_dst=bag_dest, ws_dir=ws_dir)
                Path(bag_dest).unlink()

                pages_amount = extract_pages_with_handling(self.logger, bag_info, ws_dir)
                file_groups = extract_file_groups_with_handling(self.logger, bag_info, ws_dir)

                db_workspace = await db_create_workspace(
                    user_id=py_user_action.user_id,
                    workspace_id=ws_id,
                    workspace_dir=ws_dir,
                    pages_amount=pages_amount,
                    file_groups=file_groups,
                    bag_info=bag_info,
                    state=StateWorkspace.READY,
                    details=f"Batch uploaded workspace: {workspace.filename}"
                )
                await db_increase_processing_stats_with_handling(
                    self.logger, find_user_id=py_user_action.user_id, pages_uploaded=pages_amount)
                workspace_resources.append(WorkspaceRsrc.from_db_workspace(db_workspace))
            except Exception as error:
                message = f"Failed to process workspace {workspace.filename}"
                self.logger.error(f"{message}, error: {error}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        return workspace_resources

    async def upload_batch_workspaces_from_urls(
        self, mets_urls: List[MetsUrlRequest], auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> List[WorkspaceRsrc]:
        await user_auth_with_handling(self.logger, auth)
        if len(mets_urls) > 5:
            message = "Batch upload exceeds the limit of 5 workspace urls"
            self.logger.error(message)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
        workspace_resources = []
        for mets_url_request in mets_urls:
            workspace_resource = await self.upload_workspace_from_url(
                mets_url=mets_url_request.mets_url,
                preserve_file_grps=mets_url_request.preserve_file_grps,
                mets_basename=mets_url_request.mets_basename,
                details="Batch uploaded url workspace",
                auth=auth
            )
            workspace_resources.append(workspace_resource)
        return workspace_resources
