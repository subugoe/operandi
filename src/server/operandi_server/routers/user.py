from logging import getLogger
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils.constants import AccountType, ServerApiTag
from operandi_utils.database import db_get_processing_stats, db_get_user_account_with_email
from operandi_server.models import PYUserAction, WorkflowJobRsrc, WorkspaceRsrc, WorkflowRsrc
from operandi_utils.database.models import DBProcessingStatistics
from .workflow_utils import get_workflows_of_user, get_workflow_jobs_of_user
from .workspace_utils import get_workspaces_of_user
from .user_utils import user_auth_with_handling, user_register_with_handling


class RouterUser:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.user")
        self.router = APIRouter(tags=[ServerApiTag.USER])
        self.router.add_api_route(
            path="/user/register",
            endpoint=self.user_register, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="Register a user with their e-mail and password",
            response_model=PYUserAction, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/user/login",
            endpoint=self.user_login, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Authenticate a user with their e-mail and password",
            response_model=PYUserAction, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/user/processing_stats",
            endpoint=self.user_processing_stats, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get user account statistics of the currently logged user",
            response_model=DBProcessingStatistics, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/user/workspaces",
            endpoint=self.user_workspaces, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all workspaces uploaded by the currently logged user",
            response_model=List, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/user/workflows",
            endpoint=self.user_workflows, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all workflows uploaded by the currently logged user",
            response_model=List, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/user/workflow_jobs",
            endpoint=self.user_workflow_jobs, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all workflow jobs started by the currently logged user",
            response_model=List, response_model_exclude_unset=True, response_model_exclude_none=True
        )

    async def user_login(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> PYUserAction:
        """
        Used for user authentication.
        """
        return await user_auth_with_handling(logger=self.logger, auth=auth)

    async def user_register(
        self, email: str, password: str, institution_id: str, account_type: AccountType = AccountType.USER,
        details: str = "User Account"
    ) -> PYUserAction:
        """
        Used for registration.
        There are 4 account types:
        1) ADMIN
        2) USER
        3) HARVESTER
        4) MACHINE

        Please contact the Operandi team to get your account verified.
        Otherwise, the account will be non-functional.

        Curl equivalent:
        `curl -X POST SERVER_ADDR/user/register email=example@gmail.com password=example_pass account_type=user`
        """
        db_user_account = await user_register_with_handling(
            self.logger, email=email, password=password, account_type=account_type, approved_user=False,
            details=details, institution_id=institution_id
        )
        action = f"Successfully registered a new account: {email}. " \
                 f"Please contact the OCR-D team to get your account validated before use."
        return PYUserAction.from_db_user_account(action=action, db_user_account=db_user_account)

    async def user_processing_stats(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())):
        await user_auth_with_handling(self.logger, auth)
        db_user_account = await db_get_user_account_with_email(email=auth.username)
        db_processing_stats = await db_get_processing_stats(db_user_account.user_id)
        return db_processing_stats

    async def user_workflow_jobs(
        self, auth: HTTPBasicCredentials = Depends(HTTPBasic()),
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[WorkflowJobRsrc]:
        """
        The expected datetime format: YYYY-MM-DDTHH:MM:SS, for example, 2024-12-01T18:17:15
        """
        py_user_action = await user_auth_with_handling(self.logger, auth)
        return await get_workflow_jobs_of_user(user_id=py_user_action.user_id, start_date=start_date, end_date=end_date)

    async def user_workspaces(
        self, auth: HTTPBasicCredentials = Depends(HTTPBasic()),
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[WorkspaceRsrc]:
        """
        The expected datetime format: YYYY-MM-DDTHH:MM:SS, for example, 2024-12-01T18:17:15
        """
        py_user_action = await user_auth_with_handling(self.logger, auth)
        return await get_workspaces_of_user(user_id=py_user_action.user_id, start_date=start_date, end_date=end_date)

    async def user_workflows(
        self, auth: HTTPBasicCredentials = Depends(HTTPBasic()),
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[WorkflowRsrc]:
        """
        The expected datetime format: YYYY-MM-DDTHH:MM:SS, for example, 2024-12-01T18:17:15
        """
        py_user_action = await user_auth_with_handling(self.logger, auth)
        return await get_workflows_of_user(user_id=py_user_action.user_id, start_date=start_date, end_date=end_date)
