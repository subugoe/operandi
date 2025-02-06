from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from operandi_utils.hpc.constants import HPC_NHR_JOB_DEFAULT_PARTITION
from ..constants import DEFAULT_FILE_GRP, DEFAULT_METS_BASENAME

class Resource(BaseModel):
    user_id: str = Field(..., description="The unique id of the user who created the resource")
    resource_id: str = Field(..., description="The unique id of the resource")
    resource_url: str = Field(..., description="The unique URL of the resource")
    description: str = Field(..., description="The description of the resource")
    datetime: datetime
    deleted: bool

    class Config:
        allow_population_by_field_name = True

class WorkflowArguments(BaseModel):
    workspace_id: str
    input_file_grp: Optional[str] = DEFAULT_FILE_GRP
    remove_file_grps: Optional[str] = ""
    preserve_file_grps: Optional[str] = ""
    mets_name: Optional[str] = DEFAULT_METS_BASENAME

    class Config:
        allow_population_by_field_name = True

class SbatchArguments(BaseModel):
    partition: str = HPC_NHR_JOB_DEFAULT_PARTITION  # partition to be used
    cpus: int = 4  # cpus per job allocated by default
    ram: int = 32  # RAM (in GB) per job allocated by default

    class Config:
        allow_population_by_field_name = True

class OlahdUploadArguments(BaseModel):
    username: str
    password: str
    endpoint: str

    class Config:
        allow_population_by_field_name = True

class MetsUrlRequest(BaseModel):
    mets_url: str = Field(..., description="The mets url")
    preserve_file_grps: str = Field(..., description="The file groups to be preserved")
    mets_basename: str = Field(default=DEFAULT_METS_BASENAME, description="The mets file basename")

    class Config:
        allow_population_by_field_name = True
