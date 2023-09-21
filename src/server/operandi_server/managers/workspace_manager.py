import logging
from os import remove, symlink
from shutil import rmtree
from typing import List, Union, Tuple

from ocrd import Resolver
from ocrd.workspace import Workspace
from ocrd.workspace_bagger import WorkspaceBagger

from operandi_utils.database import (
    db_create_workspace,
    db_get_workspace,
    db_update_workspace
)

from ..exceptions import (
    WorkspaceException,
    WorkspaceGoneException,
)

from .constants import (
    DEFAULT_FILE_GRP,
    DEFAULT_METS_BASENAME,
    LOG_LEVEL,
    WORKSPACES_ROUTER
)
from .resource_manager import ResourceManager
from .utils import extract_bag_info, validate_bag


class WorkspaceManager(ResourceManager):
    def __init__(
            self,
            logger_label: str = __name__,
            log_level: str = LOG_LEVEL,
            workspace_router: str = WORKSPACES_ROUTER
    ):
        super().__init__(logger_label=logger_label, log_level=log_level)
        self.log = logging.getLogger(logger_label)
        self.log.setLevel(logging.getLevelName(log_level))
        self.workspace_router = workspace_router
        self._create_resource_base_dir(self.workspace_router)

    def get_workspaces(self) -> List[Tuple[str, str]]:
        """
        Get a list of all available workspace urls.
        """
        return self.get_all_resources(self.workspace_router, local=False)

    def get_workspace_url(self, workspace_id: str):
        return self.get_resource(
            resource_router=self.workspace_router,
            resource_id=workspace_id,
            local=False
        )

    def get_workspace_path(self, workspace_id: str):
        return self.get_resource(
            resource_router=self.workspace_router,
            resource_id=workspace_id,
            local=True
        )

    async def create_workspace_from_mets_dir(self, mets_dir: str, uid: str = None) -> Tuple[Union[str, None], str]:
        workspace_id, workspace_dir = self._create_resource_dir(uid)
        symlink(mets_dir, workspace_dir)
        workspace_url = self.get_resource(self.workspace_router, workspace_id, local=False)
        return workspace_url, workspace_id

    async def create_workspace_from_zip(self, file, uid: str = None) -> Tuple[Union[str, None], str]:
        workspace_id, workspace_dir = self._create_resource_dir(self.workspace_router, uid)
        bag_dest = f"{workspace_dir}.zip"

        await self._receive_resource(file=file, resource_dest=bag_dest)
        # Remove old workspace dir (if any)
        rmtree(workspace_dir, ignore_errors=True)
        bag_info = extract_bag_info(bag_dest, workspace_dir)
        remove(bag_dest)

        await db_create_workspace(
            workspace_id=workspace_id,
            workspace_dir=workspace_dir,
            bag_info=bag_info
        )
        workspace_url = self.get_resource(self.workspace_router, workspace_id, local=False)
        return workspace_url, workspace_id

    async def create_workspace_from_mets_url(
            self,
            mets_url: str,
            file_grp: str = DEFAULT_FILE_GRP,
            mets_basename: str = DEFAULT_METS_BASENAME
    ) -> Tuple[Union[str, None], str]:
        workspace_id, workspace_dir = self._create_resource_dir(self.workspace_router)
        bag_dest = f"{workspace_dir}.zip"

        resolver = Resolver()
        # Create an OCR-D Workspace from a mets URL
        # without downloading the files referenced in the mets file
        workspace = resolver.workspace_from_url(
            mets_url=mets_url,
            clobber_mets=False,
            mets_basename=mets_basename,
            download=False
        )

        # TODO: This allows only a single file group
        #  implement for a list of file groups
        if file_grp:
            # Remove unnecessary file groups from the mets file to reduce the size
            remove_groups = [x for x in workspace.mets.file_groups if x not in file_grp]
            for remove_group in remove_groups:
                workspace.remove_file_group(remove_group, recursive=True, force=True)
            workspace.save_mets()

        # The ocrd workspace bagger automatically downloads the files/groups
        WorkspaceBagger(resolver).bag(workspace, dest=bag_dest, ocrd_identifier=workspace_id, processes=1)
        validate_bag(bag_dest)
        # Remove old workspace dir (if any)
        rmtree(workspace_dir, ignore_errors=True)
        bag_info = extract_bag_info(bag_dest, workspace_dir)

        # Remove the temporary directory
        rmtree(workspace.directory, ignore_errors=True)
        # Remove the created zip bag
        remove(bag_dest)

        await db_create_workspace(workspace_id, workspace_dir, bag_info)
        workspace_url = self.get_resource(self.workspace_router, workspace_id, local=False)
        return workspace_url, workspace_id

    async def update_workspace(self, file, workspace_id: str) -> Union[str, None]:
        """
        Update a workspace

        Delete the workspace if existing and then delegate to
        :py:func:`ocrd_webapi.workspace_manager.WorkspaceManager.create_workspace_from_zip
        """
        self._delete_resource_dir(self.workspace_router, workspace_id)
        ws_url, ws_id = await self.create_workspace_from_zip(file=file, uid=workspace_id)
        return ws_url

    # TODO: Refine this and get rid of the low level os.path bullshits
    async def get_workspace_bag(self, workspace_id: str) -> Union[str, None]:
        """
        Create workspace bag.

        The resulting zip is stored in the workspaces' directory (`self._resource_dir`).
        The Workspace could have been changed so recreation of bag-files is necessary.
        Simply zipping is not sufficient.

        Args:
             workspace_id (str): id of workspace to bag
        Returns:
            path to created bag
        """
        workspace_db = await db_get_workspace(workspace_id)
        if not workspace_db:
            return None
        bag_dest = f"{workspace_db.workspace_dir}.zip"
        mets_basename = workspace_db.mets_basename
        if not mets_basename:
            mets_basename = DEFAULT_METS_BASENAME
        resolver = Resolver()
        WorkspaceBagger(resolver).bag(
            Workspace(
                resolver,
                directory=workspace_db.workspace_dir,
                mets_basename=mets_basename
            ),
            ocrd_identifier=workspace_db.ocrd_identifier,
            dest=bag_dest,
            ocrd_mets=mets_basename,
            # This must be 1, crashes for higher values
            processes=1
        )
        return bag_dest

    async def delete_workspace(self, workspace_id: str) -> Union[str, None]:
        """
        Delete a workspace
        """
        # TODO: Separate the local storage from DB cases
        workspace_dir = self.get_resource(self.workspace_router, workspace_id, local=True)
        if not workspace_dir:
            ws = await db_get_workspace(workspace_id)
            if ws and ws.deleted:
                raise WorkspaceGoneException(f"Workspace is already deleted: {workspace_id}")
            raise WorkspaceException(f"Workspace is not existing: {workspace_id}")

        deleted_workspace_url = self.get_resource(self.workspace_router, workspace_id, local=False)
        self._delete_resource_dir(self.workspace_router, workspace_id)
        await db_update_workspace(find_workspace_id=workspace_id, deleted=True)

        return deleted_workspace_url
