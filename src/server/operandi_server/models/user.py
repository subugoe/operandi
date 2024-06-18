from pydantic import BaseModel, Field


class PYUserAction(BaseModel):
    account_type: str = Field(..., description="The type of this user")
    action: str = Field(default="Description of the user action", description="Description of the user action")
    email: str = Field(..., description="Email linked to this User")

    class Config:
        allow_population_by_field_name = True

    @staticmethod
    def create(account_type: str, action: str, email: str):
        if not action:
            action = "User Action"
        return PYUserAction(account_type=account_type, action=action, email=email)
