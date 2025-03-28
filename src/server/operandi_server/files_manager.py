import aiofiles
from io import DEFAULT_BUFFER_SIZE
from os import environ
from os.path import join
from pathlib import Path
from shutil import rmtree
from typing import Tuple
from operandi_utils import generate_id
from .constants import (
    SERVER_OTON_CONVERSIONS, SERVER_WORKFLOWS_ROUTER, SERVER_WORKFLOW_JOBS_ROUTER, SERVER_WORKSPACES_ROUTER)

class LocalFilesManager:
    def __init__(self):
        self.server_base_live_url = environ.get("OPERANDI_SERVER_URL_LIVE", None)
        if not self.server_base_live_url:
            raise ValueError("Environment variable not set: OPERANDI_SERVER_URL_LIVE")
        self.base_dir_server = environ.get("OPERANDI_SERVER_BASE_DIR", None)
        if not self.base_dir_server:
            raise ValueError("Environment variable not set: OPERANDI_SERVER_BASE_DIR")
        self.base_dirs = {
            SERVER_OTON_CONVERSIONS: join(self.base_dir_server, SERVER_OTON_CONVERSIONS),
            SERVER_WORKSPACES_ROUTER: join(self.base_dir_server, SERVER_WORKSPACES_ROUTER),
            SERVER_WORKFLOWS_ROUTER: join(self.base_dir_server, SERVER_WORKFLOWS_ROUTER),
            SERVER_WORKFLOW_JOBS_ROUTER: join(self.base_dir_server, SERVER_WORKFLOW_JOBS_ROUTER)
        }

    def __del__(self):
        pass

    def make_dir_base_resources(self):
        for key, value in self.base_dirs.items():
            Path(value).mkdir(mode=0o777, parents=True, exist_ok=True)

    def __make_dir_resource(
        self, resource_router: str, resource_id: str = "", exists_ok: bool = True
    ) -> Tuple[str, str]:
        if resource_id == "":
            resource_id = generate_id()
        resource_dir = str(join(self.base_dirs[resource_router], resource_id))
        if Path(resource_dir).is_dir():
            if not exists_ok:
                raise FileExistsError(
                    f"Failed to create resource dir '{resource_router}', already exists: {resource_dir}")
        Path(resource_dir).mkdir(mode=0o777, parents=True, exist_ok=True)
        return resource_id, resource_dir

    def make_dir_oton_conversions(self, resource_id: str = "", exists_ok: bool = True) -> Tuple[str, str]:
        return self.__make_dir_resource(SERVER_OTON_CONVERSIONS, resource_id, exists_ok)

    def make_dir_workspace(self, workspace_id: str = "", exists_ok: bool = True) -> Tuple[str, str]:
        return self.__make_dir_resource(SERVER_WORKSPACES_ROUTER, workspace_id, exists_ok)

    def make_dir_workflow(self, workflow_id: str = "", exists_ok: bool = True) -> Tuple[str, str]:
        return self.__make_dir_resource(SERVER_WORKFLOWS_ROUTER, workflow_id, exists_ok)

    def make_dir_workflow_job(self, workflow_job_id: str = "", exists_ok: bool = True) -> Tuple[str, str]:
        return self.__make_dir_resource(SERVER_WORKFLOW_JOBS_ROUTER, workflow_job_id, exists_ok)

    def __get_dir_resource(self, resource_router: str, resource_id: str) -> str:
        resource_dir = str(join(self.base_dirs[resource_router], resource_id))
        if not Path(resource_dir).is_dir():
            raise FileNotFoundError(f"Resource dir '{resource_router}' not found: {resource_dir}")
        return resource_dir

    def get_dir_workspace(self, workspace_id: str) -> str:
        return self.__get_dir_resource(SERVER_WORKSPACES_ROUTER, workspace_id)

    def get_dir_workflow(self, workflow_id: str) -> str:
        return self.__get_dir_resource(SERVER_WORKFLOWS_ROUTER, workflow_id)

    def get_dir_workflow_job(self, workflow_job_id: str) -> str:
        return self.__get_dir_resource(SERVER_WORKFLOW_JOBS_ROUTER, workflow_job_id)

    def get_url_workspace(self, workspace_id: str) -> str:
        return join(self.server_base_live_url, SERVER_WORKSPACES_ROUTER, workspace_id)

    def get_url_workflow(self, workflow_id: str) -> str:
        return join(self.server_base_live_url, SERVER_WORKFLOWS_ROUTER, workflow_id)

    def get_url_workflow_job(self, workflow_job_id: str) -> str:
        return join(self.server_base_live_url, SERVER_WORKFLOW_JOBS_ROUTER, workflow_job_id)

    def __delete_dir_resource(
        self, resource_router: str, resource_id: str, missing_ok: bool = False
    ) -> Tuple[str, str]:
        resource_dir = str(join(self.base_dirs[resource_router], resource_id))
        if not Path(resource_dir).is_dir():
            if not missing_ok:
                raise FileNotFoundError(f"Resource dir '{resource_router}' not found: {resource_dir}")
        rmtree(resource_dir, ignore_errors=True)
        return resource_id, resource_dir

    def delete_dir_workspace(self, workspace_id: str, missing_ok: bool = False) -> Tuple[str, str]:
        return self.__delete_dir_resource(SERVER_WORKSPACES_ROUTER, workspace_id, missing_ok)

    def delete_dir_workflow(self, workflow_id: str, missing_ok: bool = False) -> Tuple[str, str]:
        return self.__delete_dir_resource(SERVER_WORKFLOWS_ROUTER, workflow_id, missing_ok)

    def delete_dir_workflow_job(self, workflow_job_id: str, missing_ok: bool = False) -> Tuple[str, str]:
        return self.__delete_dir_resource(SERVER_WORKFLOW_JOBS_ROUTER, workflow_job_id, missing_ok)


async def receive_resource(file, resource_dst, chunk_size: int = DEFAULT_BUFFER_SIZE):
    async with aiofiles.open(file=resource_dst, mode="wb") as fpt:
        content = await file.read(chunk_size)
        while content:
            await fpt.write(content)
            content = await file.read(chunk_size)

# TODO: Consider making that a Singleton instance
LFMInstance = LocalFilesManager()
