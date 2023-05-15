from pydantic import BaseModel, Field
from typing import Optional

from ocrd_webapi.models.base import Job, JobState
from ocrd_webapi.models.workspace import WorkspaceRsrc


# TODO: ProcessorRsrc must inherit Resource, not BaseModel
#  in order to preserver the consistency
class ProcessorRsrc(BaseModel):
    description: str = Field(
        default='Description not provided',
        description='Description of the thing'
    )
    ref: str = Field(
        ...,
        description='link to ocrd-tool.json'
    )

    @staticmethod
    def create(processor_name: str):
        # TODO: How to to get a link to the ocrd-tool.json ?
        # Running `ocrd-.* --dump-json`
        # returns the ocrd-tool.json of a processor
        return ProcessorRsrc(
            ref=f"TODO: find a way to get a link to {processor_name}'s ocrd-tool.json",
            description="Processor"
        )

    class Config:
        allow_population_by_field_name = True


class ProcessorJobRsrc(Job):
    # Local variables:
    # resource_id: (str) - inherited from Resource -> Job
    # resource_url: (str) - inherited from Resource -> Job
    # description: (str) - inherited from Resource -> Job
    # job_state: (JobState)  - inherited from Job
    processor: Optional[ProcessorRsrc] = None
    workspace: Optional[WorkspaceRsrc] = None

    @staticmethod
    def create(job_id: str,
               job_url: str,
               processor_name: str,
               workspace_url: str,
               job_state: JobState,
               description: str = None):
        if not description:
            description = "Processor-Job"
        processor_rsrc = ProcessorRsrc.create(processor_name)
        workspace_rsrc = WorkspaceRsrc.create(workspace_url)
        return ProcessorJobRsrc(
            id=job_id,
            job_url=job_url,
            description=description,
            job_state=job_state,
            processor=processor_rsrc,
            workspace=workspace_rsrc,
        )
