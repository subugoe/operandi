from typing import Optional
from operandi_utils.constants import StateJob
from operandi_utils.database.models import DBWorkflow, DBWorkflowJob, DBWorkspace
from .base import Resource
from .workspace import WorkspaceRsrc


class WorkflowRsrc(Resource):
    # Local variables:
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    # created_by_user: (str) - inherited from Resource

    @staticmethod
    def from_db_workflow(db_workflow: DBWorkflow, workflow_url: str):
        return WorkflowRsrc(
            resource_id=db_workflow.workflow_id,
            resource_url=workflow_url,
            description=db_workflow.details,
            created_by_user=db_workflow.created_by_user
        )


class WorkflowJobRsrc(Resource):
    # Local variables:
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    # created_by_user: (str) - inherited from Resource
    job_state: Optional[StateJob] = StateJob.UNSET
    workflow_rsrc: Optional[WorkflowRsrc]
    workspace_rsrc: Optional[WorkspaceRsrc]

    @staticmethod
    def from_db_workflow_job(
        db_workflow_job: DBWorkflowJob, workflow_job_url: str,
        db_workflow: DBWorkflow, workflow_url: str,
        db_workspace: DBWorkspace, workspace_url: str
    ):
        return WorkflowJobRsrc(
            resource_id=db_workflow_job.job_id,
            resource_url=workflow_job_url,
            description=db_workflow_job.details,
            job_state=db_workflow_job.job_state,
            workflow_rsrc=WorkflowRsrc.from_db_workflow(db_workflow, workflow_url),
            workspace_rsrc=WorkspaceRsrc.from_db_workspace(db_workspace, workspace_url),
            created_by_user=db_workflow_job.created_by_user
        )
