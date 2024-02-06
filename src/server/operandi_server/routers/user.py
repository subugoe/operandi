from logging import getLogger
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_server.authentication import authenticate_user, register_user
from operandi_server.constants import ACCOUNT_TYPES
from operandi_server.exceptions import AuthenticationError, RegistrationError
from operandi_server.models import PYUserAction


class RouterUser:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.user")
        self.router = APIRouter(tags=["User"])
        self.router.add_api_route(
            path="/user/login",
            endpoint=self.user_login,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            summary="Authenticate a user with their e-mail and password",
            response_model=PYUserAction,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )
        self.router.add_api_route(
            path="/user/register",
            endpoint=self.user_register,
            methods=["GET"],
            status_code=status.HTTP_201_CREATED,
            summary="Register a user with their e-mail and password",
            response_model=PYUserAction,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )

    async def user_login(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> PYUserAction:
        """
        Used for user authentication.
        """
        email = auth.username
        password = auth.password
        if not (email and password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Basic"},
                detail="Missing e-mail or password field"
            )
        try:
            account_type = await authenticate_user(email=email, password=password)
        except AuthenticationError as error:
            self.logger.info(f"User failed to authenticate: {email}, reason: {error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Basic"},
                detail=f"Invalid login credentials or unapproved account."
            )
        return PYUserAction(account_type=account_type, action="Successfully logged!", email=email)

    async def user_register(self, email: str, password: str, account_type: str = "user") -> PYUserAction:
        """
        Used for registration.
        There are 3 account types:
        1) Administrator
        2) User
        3) Harvester

        Please contact the Operandi team to get your account verified.
        Otherwise, the account will be non-functional.

        Curl equivalent:
        `curl -X POST SERVER_ADDR/user/register email=example@gmail.com password=example_pass account_type=user`
        """
        if account_type not in ACCOUNT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                headers={"WWW-Authenticate": "Basic"},
                detail=f"Wrong account type. Must be one of: {ACCOUNT_TYPES}"
            )

        try:
            await register_user(
                email=email,
                password=password,
                account_type=account_type,
                approved_user=False
            )
        except RegistrationError as error:
            self.logger.info(f"User failed to register: {email}, reason: {error}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                headers={"WWW-Authenticate": "Basic"},
                detail=f"Failed to register user"
            )
        action = f"Successfully registered a new account: {email}. " \
                 f"Please contact the OCR-D team to get your account validated before use."
        return PYUserAction(account_type=account_type, action=action, email=email)
