from typing import Optional
from operandi_utils.constants import StateJob
from operandi_utils.database.models import DBWorkflow, DBWorkflowJob, DBWorkspace
from operandi_server.constants import SERVER_WORKFLOWS_ROUTER, SERVER_WORKFLOW_JOBS_ROUTER
from operandi_server.files_manager import get_resource_url
from .base import Resource
from .workspace import WorkspaceRsrc

class WorkflowRsrc(Resource):
    # Local variables:
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    # created_by_user: (str) - inherited from Resource
    # datetime: (datetime) - inherited from Resource

    class Config:
        allow_population_by_field_name = True

    @staticmethod
    def from_db_workflow(db_workflow: DBWorkflow):
        return WorkflowRsrc(
            resource_id=db_workflow.workflow_id,
            resource_url=get_resource_url(SERVER_WORKFLOWS_ROUTER, db_workflow.workflow_id),
            description=db_workflow.details,
            created_by_user=db_workflow.created_by_user,
            datetime=db_workflow.datetime
        )

class WorkflowJobRsrc(Resource):
    # Local variables:
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    # created_by_user: (str) - inherited from Resource
    # datetime: (datetime) - inherited from Resource
    job_state: Optional[StateJob] = StateJob.UNSET
    workflow_rsrc: Optional[WorkflowRsrc]
    workspace_rsrc: Optional[WorkspaceRsrc]

    class Config:
        allow_population_by_field_name = True

    @staticmethod
    def from_db_workflow_job(db_workflow_job: DBWorkflowJob, db_workflow: DBWorkflow, db_workspace: DBWorkspace):
        return WorkflowJobRsrc(
            resource_id=db_workflow_job.job_id,
            resource_url=get_resource_url(SERVER_WORKFLOW_JOBS_ROUTER, db_workflow_job.job_id),
            description=db_workflow_job.details,
            job_state=db_workflow_job.job_state,
            workflow_rsrc=WorkflowRsrc.from_db_workflow(db_workflow),
            workspace_rsrc=WorkspaceRsrc.from_db_workspace(db_workspace),
            created_by_user=db_workflow_job.created_by_user,
            datetime=db_workflow_job.datetime
        )
