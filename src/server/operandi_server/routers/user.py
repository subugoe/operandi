from logging import getLogger
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils.constants import AccountType, ServerApiTag
from operandi_utils.database import db_get_processing_stats, db_get_all_jobs_by_user, db_get_user_account_with_email
from operandi_server.exceptions import AuthenticationError
from operandi_server.models import PYUserAction, WorkflowJobRsrc
from operandi_utils.database.models import DBProcessingStatistics
from .user_utils import user_auth, user_register_with_handling


class RouterUser:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.user")
        self.router = APIRouter(tags=[ServerApiTag.USER])
        self.router.add_api_route(
            path="/user/login",
            endpoint=self.user_login, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Authenticate a user with their e-mail and password",
            response_model=PYUserAction, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/user/register",
            endpoint=self.user_register, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="Register a user with their e-mail and password",
            response_model=PYUserAction, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/user/processing_stats",
            endpoint=self.user_processing_stats, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get user account statistics of the current account",
            response_model=DBProcessingStatistics, response_model_exclude_unset=True, response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/user/workflow_jobs",
            endpoint=self.user_workflow_jobs, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get all workflow jobs submitted by the user",
            response_model=List[WorkflowJobRsrc], response_model_exclude_unset=True, response_model_exclude_none=True
        )

    async def user_login(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> PYUserAction:
        """
        Used for user authentication.
        """
        email = auth.username
        password = auth.password
        headers = {"WWW-Authenticate": "Basic"}
        if not (email and password):
            message = f"User login failed, missing e-mail or password field."
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers=headers, detail=message)
        try:
            db_user_account = await user_auth(email=email, password=password)
        except AuthenticationError as error:
            self.logger.error(f"{error}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers=headers, detail=str(error))
        return PYUserAction.from_db_user_account(action="Successfully logged!", db_user_account=db_user_account)

    async def user_register(
        self, email: str, password: str, institution_id: str, account_type: AccountType = AccountType.USER,
        details: str = "User Account"
    ) -> PYUserAction:
        """
        Used for registration.
        There are 3 account types:
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
        await self.user_login(auth)
        db_user_account = await db_get_user_account_with_email(email=auth.username)
        db_processing_stats = await db_get_processing_stats(db_user_account.user_id)
        return db_processing_stats

    async def user_workflow_jobs(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> List[WorkflowJobRsrc]:
        await self.user_login(auth)
        # Fetch user account details
        db_user_account = await db_get_user_account_with_email(email=auth.username)
        # Retrieve workflow jobs for the user
        workflow_jobs = await db_get_all_jobs_by_user(user_id=db_user_account.user_id)
        return workflow_jobs

