from os import listdir, mkdir, scandir
from os.path import exists, isdir, join
from pathlib import Path
from typing import List, Tuple
import aiofiles
import shutil
import logging

from ..constants import SERVER_URL
from .constants import BASE_DIR, LOG_LEVEL
from .utils import generate_id


class ResourceManager:
    def __init__(
            self,
            logger_label: str = __name__,
            log_level: str = LOG_LEVEL,
            resources_base_dir: str = BASE_DIR,
            server_url: str = SERVER_URL,
    ):
        # Logger label of this manager - passed from the child class
        self.log = logging.getLogger(logger_label)
        self.log.setLevel(logging.getLevelName(log_level))
        # Base of the server url
        self._server_url = server_url
        # Base directory for all resource managers
        self._resources_base_dir = resources_base_dir

    def _create_resource_base_dir(self, resource_router: str):
        resource_abs_path = join(self._resources_base_dir, resource_router)
        log_msg = f"base directory of resource '{resource_router}': {resource_abs_path}"
        if exists(resource_abs_path):
            self.log.info(f"Using the existing {log_msg}")
        else:
            Path(resource_abs_path).mkdir(mode=0o777, parents=True, exist_ok=True)
            self.log.info(f"Create non-existing {log_msg}")

    def get_all_resources(self, resource_router: str, local: bool) -> List[Tuple[str, str]]:
        resources = []
        for res in scandir(join(self._resources_base_dir, resource_router)):
            if res.is_dir():
                resource_id = str(res.name)
                if local:
                    resources.append((resource_id, res))
                else:
                    url = join(self._server_url, resource_router, resource_id)
                    resources.append((resource_id, url))
        return resources

    def get_resource(self, resource_router: str, resource_id: str, local: bool) -> str:
        resource_dir = join(self._resources_base_dir, resource_router, resource_id)
        if isdir(resource_dir):
            if local:
                return resource_dir
            return join(self._server_url, resource_router, resource_id)
        raise Exception(f"Resource dir not found: {resource_dir}")

    def get_resource_file(self, resource_router: str, resource_id: str, file_ext=None) -> str:
        # Wrapper, in case the underlying
        # implementation has to change
        resource_dir = join(self._resources_base_dir, resource_router, resource_id)
        for file in listdir(resource_dir):
            if file_ext and file.endswith(file_ext):
                return join(resource_dir, file)
        raise Exception(f"Resource file not found in: {resource_dir}")

    def _create_resource_dir(self, resource_router: str, resource_id: str = None) -> Tuple[str, str]:
        if resource_id is None:
            resource_id = generate_id()
        resource_dir = join(self._resources_base_dir, resource_router, resource_id)
        if exists(resource_dir):
            self.log.error(f"Cannot create: {resource_id}. Resource already exists!")
            # TODO: Raise an Exception here
        mkdir(mode=0o777, path=resource_dir)
        return resource_id, resource_dir

    def _delete_resource_dir(self, resource_router: str, resource_id: str) -> Tuple[str, str]:
        resource_dir = join(self._resources_base_dir, resource_router, resource_id)
        if isdir(resource_dir):
            shutil.rmtree(resource_dir, ignore_errors=True)
        return resource_id, resource_dir

    @staticmethod
    async def _receive_resource(file, resource_dest):
        async with aiofiles.open(resource_dest, "wb") as fpt:
            content = await file.read(1024)
            while content:
                await fpt.write(content)
                content = await file.read(1024)
