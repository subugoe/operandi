from operandi_utils.constants import StateWorkspace
from operandi_utils.database.models import DBWorkspace
from operandi_server.constants import SERVER_WORKSPACES_ROUTER
from operandi_server.files_manager import get_resource_url
from .base import Resource

class WorkspaceRsrc(Resource):
    # Local variables:
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    # created_by_user: (str) - inherited from Resource
    # datetime: (datetime) - inherited from Resource
    state: StateWorkspace = StateWorkspace.UNSET

    class Config:
        allow_population_by_field_name = True

    @staticmethod
    def from_db_workspace(db_workspace: DBWorkspace):
        return WorkspaceRsrc(
            resource_id=db_workspace.workspace_id,
            resource_url=get_resource_url(SERVER_WORKSPACES_ROUTER, db_workspace.workspace_id),
            description=db_workspace.details,
            state=db_workspace.state,
            created_by_user=db_workspace.created_by_user,
            datetime=db_workspace.datetime
        )
