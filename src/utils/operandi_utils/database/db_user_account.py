from datetime import datetime
from operandi_utils import call_sync, generate_id
from ..constants import AccountType
from .models import DBUserAccount


async def db_create_user_account(
    institution_id: str, email: str, encrypted_pass: str, salt: str, account_type: AccountType = AccountType.USER,
    approved_user: bool = False, details: str = "User Account"
) -> DBUserAccount:
    user_account = DBUserAccount(
        institution_id=institution_id,
        user_id=generate_id(),
        email=email,
        encrypted_pass=encrypted_pass,
        salt=salt,
        account_type=account_type,
        approved_user=approved_user,
        datetime=datetime.now(),
        details=details
    )
    await user_account.save()
    return user_account


@call_sync
async def sync_db_create_user_account(
    institution_id: str, email: str, encrypted_pass: str, salt: str, account_type: AccountType = AccountType.USER,
    approved_user: bool = False, details: str = "User Account"
) -> DBUserAccount:
    return await db_create_user_account(
        institution_id, email, encrypted_pass, salt, account_type, approved_user, details)


async def db_get_user_account(user_id: str) -> DBUserAccount:
    db_user_account = await DBUserAccount.find_one(DBUserAccount.user_id == user_id)
    if not db_user_account:
        raise RuntimeError(f"No DB user account entry found for user_id: {user_id}")
    return db_user_account


@call_sync
async def sync_db_get_user_account(user_id: str) -> DBUserAccount:
    return await db_get_user_account(user_id)


async def db_get_user_account_with_email(email: str) -> DBUserAccount:
    db_user_account = await DBUserAccount.find_one(DBUserAccount.email == email)
    if not db_user_account:
        raise RuntimeError(f"No DB user account entry found for email: {email}")
    return db_user_account


@call_sync
async def sync_db_get_user_account_with_email(email: str) -> DBUserAccount:
    return await db_get_user_account(email)


async def db_update_user_account(user_id: str, **kwargs) -> DBUserAccount:
    db_user_account = await db_get_user_account(user_id=user_id)
    model_keys = list(db_user_account.__dict__.keys())
    for key, value in kwargs.items():
        if key not in model_keys:
            raise ValueError(f"Field not available: {key}")
        if key == "institution_id":
            db_user_account.institution_id = value
        elif key == "email":
            db_user_account.email = value
        elif key == "encrypted_pass":
            db_user_account.encrypted_pass = value
        elif key == "salt":
            db_user_account.salt = value
        elif key == "account_type":
            db_user_account.account_type = value
        elif key == "approved_user":
            db_user_account.approved_user = value
        elif key == "deleted":
            db_user_account.deleted = value
        elif key == "details":
            db_user_account.details = value
        else:
            raise ValueError(f"Field not updatable: {key}")
    await db_user_account.save()
    return db_user_account


@call_sync
async def sync_db_update_user_account(user_id: str, **kwargs) -> DBUserAccount:
    return await db_update_user_account(user_id=user_id, **kwargs)
