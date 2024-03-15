from typing import Optional
from operandi_utils.constants import StateJob, StateWorkspace
from .base import Job, Resource
from .workspace import WorkspaceRsrc


class WorkflowRsrc(Resource):
    # Local variables:
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource

    @staticmethod
    def create(workflow_id: str, workflow_url: str, description: str = None):
        if not description:
            description = "Workflow"
        return WorkflowRsrc(
            resource_id=workflow_id,
            resource_url=workflow_url,
            description=description
        )


class WorkflowJobRsrc(Job):
    # Local variables:
    # resource_id: (str) - inherited from Resource -> Job
    # resource_url: (str) - inherited from Resource -> Job
    # description: (str) - inherited from Resource -> Job
    # job_state: (JobState)  - inherited from Job
    workflow_rsrc: Optional[WorkflowRsrc]
    workspace_rsrc: Optional[WorkspaceRsrc]

    @staticmethod
    def create(
        job_id: str,
        job_url: str,
        workflow_id: str,
        workflow_url: str,
        workspace_id: str,
        workspace_url: str,
        ws_state: StateWorkspace = StateWorkspace.UNSET,
        job_state: StateJob = StateJob.UNSET,
        description: str = None
    ):
        if not description:
            description = "Workflow-Job"
        workflow_rsrc = WorkflowRsrc.create(workflow_id=workflow_id, workflow_url=workflow_url)
        workspace_rsrc = WorkspaceRsrc.create(workspace_id=workspace_id, workspace_url=workspace_url, state=ws_state)

        return WorkflowJobRsrc(
            resource_id=job_id,
            resource_url=job_url,
            description=description,
            job_state=job_state,
            workflow_rsrc=workflow_rsrc,
            workspace_rsrc=workspace_rsrc,
        )
