from logging import getLogger
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_server.models import PYUserInfo, WorkflowJobRsrc, WorkspaceRsrc, WorkflowRsrc
from operandi_utils import create_db_query
from operandi_utils.constants import AccountType, ServerApiTag
from operandi_utils.rabbitmq import get_connection_publisher
from .user_utils import get_user_accounts, get_user_processing_stats_with_handling, user_auth_with_handling
from .workflow_utils import get_user_workflows, get_user_workflow_jobs
from .workspace_utils import get_user_workspaces


class RouterAdminPanel:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.admin_panel")

        self.logger.info(f"Trying to connect RMQ Publisher")
        self.rmq_publisher = get_connection_publisher(enable_acks=True)
        self.logger.info(f"RMQPublisher connected")

        self.router = APIRouter(tags=[ServerApiTag.ADMIN])
        self.add_api_routes(self.router)

    def __del__(self):
        if self.rmq_publisher:
            self.rmq_publisher.disconnect()

    def add_api_routes(self, router: APIRouter):
        router.add_api_route(
            path="/admin/users",
            endpoint=self.get_users, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all registered users"
        )
        router.add_api_route(
            path="/admin/processing_stats/{user_id}",
            endpoint=self.user_processing_stats, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get processing stats for a specific user by user_id"
        )
        router.add_api_route(
            path="/admin/workflow_jobs/{user_id}",
            endpoint=self.user_workflow_jobs, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all workflow jobs submitted by the user identified by user_id"
        )
        router.add_api_route(
            path="/admin/workspaces/{user_id}",
            endpoint=self.user_workspaces, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all workspaces submitted by the user identified by user_id"
        )
        router.add_api_route(
            path="/admin/workflows/{user_id}",
            endpoint=self.user_workflows, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all workflows submitted by the user identified by user_id"
        )

    async def auth_admin_with_handling(self, auth: HTTPBasicCredentials):
        py_user_action = await user_auth_with_handling(self.logger, auth)
        if py_user_action.account_type != AccountType.ADMIN:
            message = f"Admin privileges required for the endpoint"
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

    async def get_users(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> List[PYUserInfo]:
        await self.auth_admin_with_handling(auth)
        return await get_user_accounts()

    async def user_processing_stats(
        self, user_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic()),
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ):
        await self.auth_admin_with_handling(auth)
        query = create_db_query(user_id, start_date, end_date)
        return await get_user_processing_stats_with_handling(logger=self.logger, query=query)

    async def user_workflow_jobs(
        self, user_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic()),
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, hide_deleted: bool = True
    ) -> List[WorkflowJobRsrc]:
        """
        The expected datetime format: YYYY-MM-DDTHH:MM:SS, for example, 2024-12-01T18:17:15
        """
        await self.auth_admin_with_handling(auth)
        query = create_db_query(user_id, start_date, end_date, hide_deleted)
        return await get_user_workflow_jobs(logger=self.logger, rmq_publisher=self.rmq_publisher, query=query)

    async def user_workspaces(
        self, user_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic()),
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, hide_deleted: bool = True
    ) -> List[WorkspaceRsrc]:
        """
        The expected datetime format: YYYY-MM-DDTHH:MM:SS, for example, 2024-12-01T18:17:15
        """
        await self.auth_admin_with_handling(auth)
        query = create_db_query(user_id, start_date, end_date, hide_deleted)
        return await get_user_workspaces(logger=self.logger, query=query)

    async def user_workflows(
        self, user_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic()),
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, hide_deleted: bool = True
    ) -> List[WorkflowRsrc]:
        """
        The expected datetime format: YYYY-MM-DDTHH:MM:SS, for example, 2024-12-01T18:17:15
        """
        await self.auth_admin_with_handling(auth)
        query = create_db_query(user_id, start_date, end_date, hide_deleted)
        return await get_user_workflows(logger=self.logger, query=query)
