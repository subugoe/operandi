import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_server.authentication import authenticate_user, register_user
from operandi_server.exceptions import AuthenticationError, RegistrationError
from operandi_server.models import UserAction

router = APIRouter(
    tags=["User"],
)

logger = logging.getLogger(__name__)
# TODO: This may not be ideal, discussion needed
security = HTTPBasic()


@router.get("/user/login", responses={"200": {"model": UserAction}})
async def user_login(auth: HTTPBasicCredentials = Depends(security)):
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

    # Authenticate user e-mail and password
    try:
        account_type = await authenticate_user(
            email=email,
            password=password
        )
    except AuthenticationError as error:
        logger.info(f"User failed to authenticate: {email}, reason: {error}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
            detail=f"Invalid login credentials or unapproved account."
        )

    return UserAction(account_type=account_type, action="Successfully logged!", email=email)


@router.post("/user/register", responses={"201": {"model": UserAction}})
async def user_register(email: str, password: str, account_type: str = "user"):
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
    account_types = ["user", "administrator", "harvester"]
    if account_type not in account_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers={"WWW-Authenticate": "Basic"},
            detail=f"Wrong account type. Must be one of: {account_types}"
        )

    try:
        await register_user(
            email=email,
            password=password,
            account_type=account_type,
            approved_user=False
        )
    except RegistrationError as error:
        logger.info(f"User failed to register: {email}, reason: {error}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            headers={"WWW-Authenticate": "Basic"},
            detail=f"Failed to register user"
        )
    action = f"Successfully registered new account: {email}. " \
             f"Please contact the OCR-D team to get your account validated."
    return UserAction(email=email, action=action)
