from hashlib import sha512
from random import random
from typing import Tuple

def get_random_salt() -> str:
    return sha512(f"{hash(str(random()))}".encode("utf-8")).hexdigest()[:8]

def get_hex_digest(salt: str, plain_password: str):
    return sha512(f"{salt}{plain_password}".encode("utf-8")).hexdigest()

def encrypt_password(plain_password: str) -> Tuple[str, str]:
    salt = get_random_salt()
    hashed_password = get_hex_digest(salt, plain_password)
    encrypted_password = f"{salt}${hashed_password}"
    return salt, encrypted_password

def validate_password(plain_password: str, encrypted_password: str) -> bool:
    salt, hashed_password = encrypted_password.split(sep='$', maxsplit=1)
    return hashed_password == get_hex_digest(salt, plain_password)
