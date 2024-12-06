from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from hashlib import sha512
from random import random
from typing import Tuple

from operandi_utils.constants import AccountType
from operandi_utils.database import (
    db_create_processing_stats, db_create_user_account, db_get_user_account, db_get_user_account_with_email,
    DBUserAccount)
from operandi_server.models import PYUserAction


async def create_user_if_not_available(
    logger, username: str, password: str, account_type: AccountType, institution_id: str, approved_user: bool = False,
    details: str = "User Account"
) -> DBUserAccount:
    try:
        await db_get_user_account_with_email(email=username)
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
    salt, encrypted_password = encrypt_password(password)
    try:
        await db_get_user_account(email)
    except RuntimeError:
        # No user existing with the provided e-mail, register
        db_user_account = await db_create_user_account(
            institution_id=institution_id, email=email, encrypted_pass=encrypted_password, salt=salt,
            account_type=account_type, approved_user=approved_user, details=details)
        await db_create_processing_stats(institution_id=db_user_account.institution_id, user_id=db_user_account.user_id)
        return db_user_account
    message = f"Another user is already registered with email: {email}"
    logger.error(f"{message}")
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, headers=headers, detail=message)


def encrypt_password(plain_password: str) -> Tuple[str, str]:
    salt = get_random_salt()
    hashed_password = get_hex_digest(salt, plain_password)
    encrypted_password = f"{salt}${hashed_password}"
    return salt, encrypted_password


def get_hex_digest(salt: str, plain_password: str):
    return sha512(f"{salt}{plain_password}".encode("utf-8")).hexdigest()


def get_random_salt() -> str:
    return sha512(f"{hash(str(random()))}".encode("utf-8")).hexdigest()[:8]


def validate_password(plain_password: str, encrypted_password: str) -> bool:
    salt, hashed_password = encrypted_password.split(sep='$', maxsplit=1)
    return hashed_password == get_hex_digest(salt, plain_password)
