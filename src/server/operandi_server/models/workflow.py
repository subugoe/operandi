from typing import List, Optional
from operandi_utils.constants import StateJob
from operandi_utils.database.models import DBWorkflow, DBWorkflowJob, DBWorkspace
from operandi_server.files_manager import LFMInstance
from .base import Resource
from .workspace import WorkspaceRsrc

class WorkflowRsrc(Resource):
    # Local variables:
    # used_id: (str) - inherited from Resource
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    # created_by_user: (str) - inherited from Resource
    # datetime: (datetime) - inherited from Resource
    # deleted: bool - inherited from Resource
    uses_mets_server: bool
    executable_steps: List[str]
    producible_file_groups: List[str]

    class Config:
        allow_population_by_field_name = True

    @staticmethod
    def from_db_workflow(db_workflow: DBWorkflow):
        return WorkflowRsrc(
            user_id=db_workflow.user_id,
            resource_id=db_workflow.workflow_id,
            resource_url=LFMInstance.get_url_workflow(db_workflow.workflow_id),
            description=db_workflow.details,
            uses_mets_server=db_workflow.uses_mets_server,
            executable_steps=db_workflow.executable_steps,
            producible_file_groups=db_workflow.producible_file_groups,
            datetime=db_workflow.datetime,
            deleted=db_workflow.deleted
        )

class WorkflowJobRsrc(Resource):
    # Local variables:
    # used_id: (str) - inherited from Resource
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    # created_by_user: (str) - inherited from Resource
    # datetime: (datetime) - inherited from Resource
    # deleted: bool - inherited from Resource
    job_state: Optional[StateJob] = StateJob.UNSET
    workflow_rsrc: Optional[WorkflowRsrc]
    workspace_rsrc: Optional[WorkspaceRsrc]

    class Config:
        allow_population_by_field_name = True

    @staticmethod
    def from_db_workflow_job(db_workflow_job: DBWorkflowJob, db_workflow: DBWorkflow, db_workspace: DBWorkspace):
        return WorkflowJobRsrc(
            user_id=db_workflow_job.user_id,
            resource_id=db_workflow_job.job_id,
            resource_url=LFMInstance.get_url_workflow_job(db_workflow_job.job_id),
            description=db_workflow_job.details,
            job_state=db_workflow_job.job_state,
            workflow_rsrc=WorkflowRsrc.from_db_workflow(db_workflow),
            workspace_rsrc=WorkspaceRsrc.from_db_workspace(db_workspace),
            datetime=db_workflow_job.datetime,
            deleted=db_workflow.deleted
        )
