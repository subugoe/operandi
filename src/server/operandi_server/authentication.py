from hashlib import sha512
from random import random
from typing import Tuple

from operandi_utils.database.database import create_user, get_user
from .exceptions import AuthenticationError, RegistrationError


async def authenticate_user(email: str, password: str):
    db_user = await get_user(email=email)
    if not db_user:
        raise AuthenticationError(f"User not found: {email}")
    password_status = validate_password(
        plain_password=password,
        encrypted_password=db_user.encrypted_pass
    )
    if not password_status:
        raise AuthenticationError(f"Wrong credentials for: {email}")
    if not db_user.approved_user:
        raise AuthenticationError(f"The account was not approved by the admin yet.")


async def register_user(email: str, password: str, approved_user=False):
    salt, encrypted_password = encrypt_password(password)
    db_user = await get_user(email)
    if db_user:
        raise RegistrationError(f"User is already registered: {email}")
    created_user = await create_user(
        email=email,
        encrypted_pass=encrypted_password,
        salt=salt,
        approved_user=approved_user
    )
    if not created_user:
        raise RegistrationError(f"Failed to register user: {email}")


def encrypt_password(plain_password: str) -> Tuple[str, str]:
    salt = get_random_salt()
    hashed_password = get_hex_digest(salt, plain_password)
    encrypted_password = f'{salt}${hashed_password}'
    return salt, encrypted_password


def get_hex_digest(salt: str, plain_password: str):
    return sha512(f'{salt}{plain_password}'.encode('utf-8')).hexdigest()


def get_random_salt() -> str:
    return sha512(f'{hash(str(random()))}'.encode('utf-8')).hexdigest()[:8]


def validate_password(plain_password: str, encrypted_password: str) -> bool:
    salt, hashed_password = encrypted_password.split('$', 1)
    return hashed_password == get_hex_digest(salt, plain_password)
