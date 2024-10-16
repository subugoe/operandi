from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from operandi_utils.hpc.constants import HPC_NHR_JOB_DEFAULT_PARTITION
from ..constants import DEFAULT_FILE_GRP, DEFAULT_METS_BASENAME

class Resource(BaseModel):
    resource_id: str = Field(..., description="ID of this thing")
    resource_url: str = Field(..., description="URL of this thing")
    description: str = Field(..., description="Description of the thing")
    created_by_user: str = Field(..., description="The user who created that resource")
    datetime: datetime

    class Config:
        allow_population_by_field_name = True

class WorkflowArguments(BaseModel):
    workspace_id: str
    input_file_grp: Optional[str] = DEFAULT_FILE_GRP
    remove_file_grps: Optional[str] = ""
    mets_name: Optional[str] = DEFAULT_METS_BASENAME

    class Config:
        allow_population_by_field_name = True

class SbatchArguments(BaseModel):
    partition: str = HPC_NHR_JOB_DEFAULT_PARTITION  # partition to be used
    cpus: int = 4  # cpus per job allocated by default
    ram: int = 32  # RAM (in GB) per job allocated by default

    class Config:
        allow_population_by_field_name = True
