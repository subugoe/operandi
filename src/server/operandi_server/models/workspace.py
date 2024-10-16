from typing import Optional
from operandi_utils.constants import StateWorkspace
from .base import Resource


class WorkspaceRsrc(Resource):
    # Local variables:
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    state: StateWorkspace = StateWorkspace.UNSET
    created_by_user: Optional[str]

    @staticmethod
    def create(workspace_id: str, workspace_url: str, state: StateWorkspace, description: str = None,
               created_by_user: str = None):
        if not description:
            description = "Workspace"
        if not created_by_user:
            created_by_user = ""
        return WorkspaceRsrc(
            resource_id=workspace_id, resource_url=workspace_url, description=description, state=state,
            created_by_user=created_by_user)
