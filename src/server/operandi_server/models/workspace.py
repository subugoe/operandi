from operandi_utils.constants import StateWorkspace
from operandi_utils.database.models import DBWorkspace
from .base import Resource


class WorkspaceRsrc(Resource):
    # Local variables:
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    # created_by_user: (str) - inherited from Resource
    state: StateWorkspace = StateWorkspace.UNSET

    @staticmethod
    def from_db_workspace(db_workspace: DBWorkspace, workspace_url: str):
        return WorkspaceRsrc(
            resource_id=db_workspace.workspace_id, resource_url=workspace_url, description=db_workspace.details,
            state=db_workspace.state, created_by_user=db_workspace.created_by_user
        )
