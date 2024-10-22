from pydantic import BaseModel, Field
from operandi_utils.constants import AccountType
from operandi_utils.database.models import DBUserAccount


class PYUserAction(BaseModel):
    email: str = Field(..., description="Email linked to this User")
    account_type: AccountType = Field(AccountType.UNSET, description="The type of this user")
    action: str = Field(..., description="Description of the user action")

    class Config:
        allow_population_by_field_name = True

    @staticmethod
    def from_db_user_account(action: str, db_user_account: DBUserAccount):
        return PYUserAction(
            email=db_user_account.email,
            account_type=db_user_account.account_type,
            action=action
        )
