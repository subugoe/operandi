from pydantic import BaseModel, Field


class UserAction(BaseModel):
    email: str = Field(
        ...,  # the field is required, no default set
        description='Email linked to this User'
    )
    action: str = Field(
        default='Description of the user action',
        description='Description of the user action'
    )

    class Config:
        allow_population_by_field_name = True

    @staticmethod
    def create(email: str, action: str):
        if not action:
            action = "User Action"
        return UserAction(email=email, action=action)
