from operandi_utils.constants import StateWorkspace
from .base import Resource


class WorkspaceRsrc(Resource):
    # Local variables:
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    state: StateWorkspace = StateWorkspace.UNSET

    @staticmethod
    def create(workspace_id: str, workspace_url: str, state: StateWorkspace, description: str = None):
        if not description:
            description = "Workspace"
        return WorkspaceRsrc(
            resource_id=workspace_id,
            resource_url=workspace_url,
            description=description,
            state=state
        )
