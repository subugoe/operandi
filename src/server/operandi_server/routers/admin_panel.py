from logging import getLogger
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_server.models import PYUserInfo, WorkflowJobRsrc
from operandi_utils.constants import AccountType, ServerApiTag
from operandi_utils.database import db_get_all_user_accounts, db_get_processing_stats, db_get_all_jobs_by_user, db_get_workflow, db_get_workspace
from operandi_utils.utils import send_bag_to_ola_hd
from .user import RouterUser
from .workspace_utils import create_workspace_bag, get_db_workspace_with_handling, validate_bag_with_handling


class RouterAdminPanel:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.user")
        self.user_authenticator = RouterUser()
        self.router = APIRouter(tags=[ServerApiTag.ADMIN])
        self.router.add_api_route(
            path="/admin/push_to_ola_hd",
            endpoint=self.push_to_ola_hd, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="Push a workspace to Ola-HD service"
        )
        self.router.add_api_route(
            path="/admin/users",
            endpoint=self.get_users, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all registered users"
        )
        self.router.add_api_route(
            path="/admin/processing_stats/{user_id}",
            endpoint=self.get_processing_stats_for_user, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get processing stats for a specific user by user_id"
        )
        self.router.add_api_route(
            path="/admin/{user_id}/workflow_jobs",
            endpoint=self.user_workflow_jobs, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all workflow jobs submitted by the user identified by user_id"
        )
    async def push_to_ola_hd(self, workspace_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())):
        py_user_action = await self.user_authenticator.user_login(auth)
        if py_user_action.account_type != AccountType.ADMIN:
            message = f"Admin privileges required for the endpoint"
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
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
        # Authenticate the user and ensure they have admin privileges
        py_user_action = await self.user_authenticator.user_login(auth)
        if py_user_action.account_type != AccountType.ADMIN:
            message = "Admin privileges required for the endpoint"
            self.logger.error(message)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
        
        users = await db_get_all_user_accounts()
        return [PYUserInfo.from_db_user_account(user) for user in users]

    async def get_processing_stats_for_user(self, user_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())):
        # Authenticate the admin user
        py_user_action = await self.user_authenticator.user_login(auth)
        if py_user_action.account_type != AccountType.ADMIN:
            message = f"Admin privileges required for the endpoint"
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

        # Retrieve the processing stats for the specified user
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

        # Return the processing stats in the response model
        return db_processing_stats
    async def user_workflow_jobs(
            self,
            user_id: str,
            auth: HTTPBasicCredentials = Depends(HTTPBasic()),
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List:
        # Authenticate the admin user
        py_user_action = await self.user_authenticator.user_login(auth)
        if py_user_action.account_type != AccountType.ADMIN:
            message = f"Admin privileges required for the endpoint"
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
        # Retrieve workflow jobs for the user identified with user_id with optional date filtering
        db_workflow_jobs = await db_get_all_jobs_by_user(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        response = []
        for db_workflow_job in db_workflow_jobs:
            db_workflow = await db_get_workflow(db_workflow_job.workflow_id)
            db_workspace = await db_get_workspace(db_workflow_job.workspace_id)
            response.append(WorkflowJobRsrc.from_db_workflow_job(db_workflow_job, db_workflow, db_workspace))
        return response