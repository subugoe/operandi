from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import List

from operandi_utils.constants import AccountType
from operandi_utils.database import (
    db_create_processing_stats, db_create_user_account, db_get_all_user_accounts, db_get_user_account,
    db_get_user_account_with_email, db_get_processing_stats, DBProcessingStatistics, DBUserAccount)
from operandi_server.models import PYUserAction, PYUserInfo
from .password_utils import encrypt_password, validate_password


async def create_user_if_not_available(
    logger, username: str, password: str, account_type: AccountType, institution_id: str, approved_user: bool = False,
    details: str = "User Account"
) -> DBUserAccount:
    try:
        return await db_get_user_account_with_email(email=username)
    except RuntimeError:
        return await user_register_with_handling(
            logger, email=username, password=password, account_type=account_type, approved_user=approved_user,
            details=details, institution_id=institution_id)

async def user_auth_with_handling(
    logger, auth: HTTPBasicCredentials = Depends(HTTPBasic()), headers=None
) -> PYUserAction:
    email = auth.username
    password = auth.password
    if headers is None:
        headers = {"WWW-Authenticate": "Basic"}
    if not (email and password):
        message = f"User login failed, missing e-mail or password field."
        logger.error(f"{message}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers=headers, detail=message)
    try:
        db_user_account = await db_get_user_account_with_email(email=email)
    except RuntimeError:
        message = f"Not found user account for email: {email}"
        logger.error(f"{message}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, headers=headers, detail=message)
    if not db_user_account.approved_user:
        message = f"The account has not been approved by the admin yet."
        logger.error(f"{message}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers=headers, detail=message)
    password_status = validate_password(plain_password=password, encrypted_password=db_user_account.encrypted_pass)
    if not password_status:
        message = f"Wrong credentials for email: {email}"
        logger.error(f"{message}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers=headers, detail=message)
    return PYUserAction.from_db_user_account(action="Successfully logged!", db_user_account=db_user_account)

async def user_register_with_handling(
    logger, email: str, password: str, account_type: AccountType, institution_id: str, approved_user: bool = False,
    details: str = "User Account", headers=None
) -> DBUserAccount:
    if headers is None:
        headers = {"WWW-Authenticate": "Basic"}
    if account_type not in AccountType:
        message = f"Wrong account type. Must be one of: {AccountType}"
        logger.error(f"{message}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, headers=headers, detail=message)
    try:
        await db_get_user_account(email)
    except RuntimeError:
        salt, encrypted_password = encrypt_password(password)
        # No user existing with the provided e-mail, register
        db_user_account = await db_create_user_account(
            institution_id=institution_id, email=email, encrypted_pass=encrypted_password, salt=salt,
            account_type=account_type, approved_user=approved_user, details=details)
        await db_create_processing_stats(institution_id=db_user_account.institution_id, user_id=db_user_account.user_id)
        return db_user_account
    message = f"Another user is already registered with email: {email}"
    logger.error(f"{message}")
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, headers=headers, detail=message)

async def get_user_processing_stats_with_handling(logger, user_id: str) -> DBProcessingStatistics:
    try:
        db_processing_stats = await db_get_processing_stats(user_id=user_id)
    except RuntimeError as error:
        message = f"Processing stats not found for the user_id: {user_id}"
        logger.error(f"{message}, error: {error}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
    return db_processing_stats

async def get_user_accounts() -> List[PYUserInfo]:
    users = await db_get_all_user_accounts()
    return [PYUserInfo.from_db_user_account(user) for user in users]
