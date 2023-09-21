from operandi_utils import call_sync
from .models import DBUserAccount


async def db_create_user_account(
        email: str,
        encrypted_pass: str,
        salt: str,
        account_type: str,
        approved_user: bool = False
) -> DBUserAccount:
    user_account = DBUserAccount(
        email=email,
        encrypted_pass=encrypted_pass,
        salt=salt,
        account_type=account_type,
        approved_user=approved_user
    )
    await user_account.save()
    return user_account


@call_sync
async def sync_db_create_user_account(
        email: str,
        encrypted_pass: str,
        salt: str,
        account_type: str,
        approved_user: bool = False
) -> DBUserAccount:
    return await db_create_user_account(email, encrypted_pass, salt, account_type, approved_user)


async def db_get_user_account(email: str) -> DBUserAccount:
    db_user_account = await DBUserAccount.find_one(DBUserAccount.email == email)
    if not db_user_account:
        raise RuntimeError(f"No DB user account entry found for e-mail: {email}")
    return db_user_account


@call_sync
async def sync_db_get_user_account(email: str) -> DBUserAccount:
    return await db_get_user_account(email)


async def db_update_user_account(find_email: str, **kwargs) -> DBUserAccount:
    db_user_account = await DBUserAccount.find_one(DBUserAccount.email == find_email)
    if not db_user_account:
        raise RuntimeError(f"No DB user account entry found for email: {find_email}")
    model_keys = list(db_user_account.__dict__.keys())
    for key, value in kwargs.items():
        if key not in model_keys:
            raise ValueError(f"Field not available: {key}")
        if key == 'email':
            db_user_account.email = value
        elif key == 'encrypted_pass':
            db_user_account.encrypted_pass = value
        elif key == 'salt':
            db_user_account.salt = value
        elif key == 'account_type':
            db_user_account.account_type = value
        elif key == 'approved_user':
            db_user_account.approved_user = value
        elif key == 'deleted':
            db_user_account.deleted = value
        else:
            raise ValueError(f"Field not updatable: {key}")
    await db_user_account.save()
    return db_user_account


@call_sync
async def sync_db_update_user_account(find_email: str, **kwargs) -> DBUserAccount:
    return await db_update_user_account(find_email=find_email, **kwargs)
