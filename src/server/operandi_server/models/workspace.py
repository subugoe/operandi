from typing import List, Optional
from operandi_utils.constants import StateWorkspace
from operandi_utils.database.models import DBWorkspace
from operandi_server.constants import SERVER_WORKSPACES_ROUTER
from operandi_server.files_manager import get_resource_url
from .base import Resource

class WorkspaceRsrc(Resource):
    # Local variables:
    # used_id: (str) - inherited from Resource
    # resource_id: (str) - inherited from Resource
    # resource_url: (str) - inherited from Resource
    # description: (str) - inherited from Resource
    # created_by_user: (str) - inherited from Resource
    # datetime: (datetime) - inherited from Resource
    pages_amount: int
    file_groups: List[str]
    state: StateWorkspace = StateWorkspace.UNSET
    ocrd_identifier: Optional[str]
    bagit_profile_identifier: Optional[str]
    ocrd_base_version_checksum: Optional[str]
    mets_basename: Optional[str]
    bag_info_adds: Optional[dict]

    class Config:
        allow_population_by_field_name = True

    @staticmethod
    def from_db_workspace(db_workspace: DBWorkspace):
        return WorkspaceRsrc(
            user_id=db_workspace.user_id,
            resource_id=db_workspace.workspace_id,
            resource_url=get_resource_url(SERVER_WORKSPACES_ROUTER, db_workspace.workspace_id),
            description=db_workspace.details,
            pages_amount=db_workspace.pages_amount,
            file_groups=db_workspace.file_groups,
            state=db_workspace.state,
            datetime=db_workspace.datetime,
            ocrd_identifier=db_workspace.ocrd_identifier,
            bagit_profile_identifier=db_workspace.bagit_profile_identifier,
            ocrd_base_version_checksum=db_workspace.ocrd_base_version_checksum,
            mets_basename=db_workspace.mets_basename,
            bag_info_add=db_workspace.bag_info_adds
        )
