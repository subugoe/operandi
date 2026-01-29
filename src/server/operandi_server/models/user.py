from pydantic import BaseModel, ConfigDict, Field
from operandi_utils.constants import AccountType
from operandi_utils.database.models import DBUserAccount


class PYUserAction(BaseModel):
    model_config = ConfigDict(validate_by_name=True)
    institution_id: str = Field(..., description="Institution id of the user")
    user_id: str = Field(..., description="Unique id of the user")
    email: str = Field(..., description="Email linked to this User")
    account_type: AccountType = Field(AccountType.UNSET, description="The type of this user")
    approved_user: bool = Field(False, description="Whether the account was admin approved and fully functional")
    details: str = Field(..., description="More details about the account")
    action: str = Field(..., description="Description of the user action")

    @staticmethod
    def from_db_user_account(action: str, db_user_account: DBUserAccount):
        return PYUserAction(
            institution_id=db_user_account.institution_id,
            user_id=db_user_account.user_id,
            email=db_user_account.email,
            account_type=db_user_account.account_type,
            approved_user=db_user_account.approved_user,
            details=db_user_account.details,
            action=action
        )


class PYUserInfo(BaseModel):
    model_config = ConfigDict(validate_by_name=True)
    institution_id: str = Field(..., description="Institution id of the user")
    user_id: str = Field(..., description="Unique id of the user")
    email: str = Field(..., description="Email linked to this User")
    account_type: AccountType = Field(AccountType.UNSET, description="The type of this user")
    approved_user: bool = Field(False, description="Whether the account was admin approved and fully functional")
    details: str = Field(..., description="More details about the account")

    @staticmethod
    def from_db_user_account(db_user_account: DBUserAccount):
        return PYUserInfo(
            institution_id=db_user_account.institution_id,
            user_id=db_user_account.user_id,
            email=db_user_account.email,
            account_type=db_user_account.account_type,
            approved_user=db_user_account.approved_user,
            details=db_user_account.details
        )
