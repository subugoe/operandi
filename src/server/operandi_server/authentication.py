from hashlib import sha512
from random import random
from typing import Tuple

from operandi_utils.constants import AccountTypes
from operandi_utils.database import db_create_user_account, db_get_user_account
from operandi_server.exceptions import AuthenticationError, RegistrationError


async def create_user_if_not_available(
    username: str, password: str, account_type: str, approved_user: bool = False, details: str = "User Account"):
    # If the account is not available in the DB, create it
    try:
        await authenticate_user(username, password)
    except AuthenticationError:
        # TODO: Note that this account is never removed from
        #  the DB automatically in the current implementation
        await register_user(
            email=username, password=password, account_type=account_type, approved_user=approved_user, details=details)


async def authenticate_user(email: str, password: str) -> str:
    try:
        db_user = await db_get_user_account(email=email)
    except RuntimeError:
        raise AuthenticationError(f"Not found user account for email: {email}")
    password_status = validate_password(plain_password=password, encrypted_password=db_user.encrypted_pass)
    if not password_status:
        raise AuthenticationError(f"Wrong credentials for email: {email}")
    if not db_user.approved_user:
        raise AuthenticationError(f"The account has not been approved by the admin yet.")
    return db_user.account_type


async def register_user(
    email: str, password: str, account_type: str, approved_user: bool = False, details: str = "User Account"):
    salt, encrypted_password = encrypt_password(password)
    try:
        await db_get_user_account(email)
    except RuntimeError:
        # No user existing with the provided e-mail, register
        await db_create_user_account(
            email=email, encrypted_pass=encrypted_password, salt=salt, account_type=account_type,
            approved_user=approved_user, details=details)
        return
    raise RegistrationError(f"Another user is already registered with email: {email}")


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
