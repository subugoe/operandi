from pydantic import BaseModel, Field
from typing import Optional

from operandi_utils import StateJob


class Resource(BaseModel):
    resource_id: str = Field(..., description="ID of this thing")
    resource_url: str = Field(..., description="URL of this thing")
    description: str = Field(default="Description of the thing", description="Description of the thing")

    class Config:
        allow_population_by_field_name = True


class Job(Resource):
    # Local variables:
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    job_state: Optional[StateJob] = StateJob.UNSET

    class Config:
        allow_population_by_field_name = True


class WorkflowArguments(BaseModel):
    workspace_id: str
    input_file_grp: Optional[str] = "DEFAULT"
    remove_file_grps: Optional[str] = ""
    mets_name: Optional[str] = "mets.xml"


class SbatchArguments(BaseModel):
    cpus: int = 4  # cpus per job allocated by default
    ram: int = 32  # RAM (in GB) per job allocated by default
