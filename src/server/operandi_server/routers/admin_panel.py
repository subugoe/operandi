from logging import getLogger
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_server.models import PYUserInfo, WorkflowJobRsrc, WorkspaceRsrc, WorkflowRsrc
from operandi_utils.constants import AccountType, ServerApiTag
from operandi_utils.database import db_get_all_user_accounts, db_get_processing_stats
from operandi_utils.utils import send_bag_to_ola_hd
from .user_utils import user_auth_with_handling
from .workflow_utils import get_workflows_of_user, get_workflow_jobs_of_user
from .workspace_utils import (
    create_workspace_bag, get_workspaces_of_user, get_db_workspace_with_handling, validate_bag_with_handling
)

class RouterAdminPanel:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.user")
        self.router = APIRouter(tags=[ServerApiTag.ADMIN])
        self.router.add_api_route(
            path="/admin/users",
            endpoint=self.get_users, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all registered users"
        )
        self.router.add_api_route(
            path="/admin/processing_stats/{user_id}",
            endpoint=self.user_processing_stats, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get processing stats for a specific user by user_id"
        )
        self.router.add_api_route(
            path="/admin/workflow_jobs/{user_id}",
            endpoint=self.user_workflow_jobs, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all workflow jobs submitted by the user identified by user_id"
        )
        self.router.add_api_route(
            path="/admin/workspaces/{user_id}",
            endpoint=self.user_workspaces, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all workspaces submitted by the user identified by user_id"
        )
        self.router.add_api_route(
            path="/admin/workflows/{user_id}",
            endpoint=self.user_workflows, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all workflows submitted by the user identified by user_id"
        )
        self.router.add_api_route(
            path="/admin/push_to_ola_hd",
            endpoint=self.push_to_ola_hd, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="Push a workspace to Ola-HD service"
        )

    async def auth_admin_with_handling(self, auth: HTTPBasicCredentials):
        py_user_action = await user_auth_with_handling(self.logger, auth)
        if py_user_action.account_type != AccountType.ADMIN:
            message = f"Admin privileges required for the endpoint"
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

    async def push_to_ola_hd(self, workspace_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())):
        await self.auth_admin_with_handling(auth)
        db_workspace = await get_db_workspace_with_handling(self.logger, workspace_id=workspace_id)
        try:
            bag_dst = create_workspace_bag(db_workspace=db_workspace)
        except Exception as error:
            message = f"Failed to create workspace bag for: {workspace_id}"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
        validate_bag_with_handling(self.logger, bag_dst=bag_dst)

        try:
            pid = send_bag_to_ola_hd(path_to_bag=bag_dst)
        except Exception as error:
            message = "Failed to send bag to Ola-HD service"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

        response_message = {
            "message": f"Workspace bag of id: {workspace_id} was pushed to the Ola-HD service",
            "pid": pid
        }
        return response_message

    async def get_users(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())):
        await self.auth_admin_with_handling(auth)
        users = await db_get_all_user_accounts()
        return [PYUserInfo.from_db_user_account(user) for user in users]

    async def user_processing_stats(self, user_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())):
        await self.auth_admin_with_handling(auth)
        try:
            db_processing_stats = await db_get_processing_stats(user_id)
            if not db_processing_stats:
                message = f"Processing stats not found for the user_id: {user_id}"
                self.logger.error(message)
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        except Exception as error:
            message = f"Failed to fetch processing stats for user_id: {user_id}, error: {error}"
            self.logger.error(message)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
        return db_processing_stats

    async def user_workflow_jobs(
        self, user_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic()),
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[WorkflowJobRsrc]:
        """
        The expected datetime format: YYYY-MM-DDTHH:MM:SS, for example, 2024-12-01T18:17:15
        """
        await self.auth_admin_with_handling(auth)
        return await get_workflow_jobs_of_user(user_id=user_id, start_date=start_date, end_date=end_date)

    async def user_workspaces(
        self, user_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic()),
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[WorkspaceRsrc]:
        """
        The expected datetime format: YYYY-MM-DDTHH:MM:SS, for example, 2024-12-01T18:17:15
        """
        await self.auth_admin_with_handling(auth)
        return await get_workspaces_of_user(user_id=user_id, start_date=start_date, end_date=end_date)

    async def user_workflows(
        self, user_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic()),
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[WorkflowRsrc]:
        """
        The expected datetime format: YYYY-MM-DDTHH:MM:SS, for example, 2024-12-01T18:17:15
        """
        await self.auth_admin_with_handling(auth)
        return await get_workflows_of_user(user_id=user_id, start_date=start_date, end_date=end_date)
