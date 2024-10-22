from logging import getLogger
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils.constants import AccountTypes
from operandi_server.exceptions import AuthenticationError, RegistrationError
from operandi_server.models import PYUserAction
from .constants import ServerApiTags
from .user_utils import authenticate_user, register_user


class RouterUser:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.user")
        self.auth_headers = {"WWW-Authenticate": "Basic"}
        self.router = APIRouter(tags=[ServerApiTags.USER])
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
            path="/user_stats",
            endpoint=self.user_processing_stats, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get user account statistics of the current account",
            response_model=PYUserAction, response_model_exclude_unset=True, response_model_exclude_none=True
        )

    async def user_login(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> PYUserAction:
        """
        Used for user authentication.
        """
        email = auth.username
        password = auth.password
        if not (email and password):
            message = f"User login failed, missing e-mail or password field."
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers=self.auth_headers, detail=message)
        try:
            account_type = await authenticate_user(email=email, password=password)
        except AuthenticationError as error:
            message = f"Invalid login credentials or unapproved account."
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers=self.auth_headers, detail=message)
        return PYUserAction(email=email, account_type=account_type, action="Successfully logged!")

    async def user_register(
        self, email: str, password: str, institution_id: str, account_type: str = "USER",
        details: str = "User Account"
    ) -> PYUserAction:
        """
        Used for registration.
        There are 3 account types:
        1) ADMIN
        2) USER
        3) HARVESTER

        Please contact the Operandi team to get your account verified.
        Otherwise, the account will be non-functional.

        Curl equivalent:
        `curl -X POST SERVER_ADDR/user/register email=example@gmail.com password=example_pass account_type=user`
        """
        account_types = ["USER", "HARVESTER", "ADMIN"]
        if account_type not in account_types:
            message = f"Wrong account type. Must be one of: {account_types}"
            self.logger.error(f"{message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, headers=self.auth_headers, detail=message)
        try:
            await register_user(
                email=email, password=password, account_type=account_type, approved_user=False, details=details,
                institution_id=institution_id
            )
        except RegistrationError as error:
            message = f"User failed to register: {email}, reason: {error}"
            self.logger.error(f"{message}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, headers=self.auth_headers, detail=message)
        action = f"Successfully registered a new account: {email}. " \
                 f"Please contact the OCR-D team to get your account validated before use."
        return PYUserAction(email=email, account_type=account_type, action=action)

    async def user_processing_stats(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())):
        pass