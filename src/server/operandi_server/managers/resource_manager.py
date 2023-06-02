from os import listdir, mkdir, scandir
from os.path import exists, isdir, join
from pathlib import Path
from typing import List, Union, Tuple
import aiofiles
import shutil
import logging

from ..constants import SERVER_URL
from .constants import BASE_DIR
from .utils import generate_id


class ResourceManager:
    # Warning: Don't change the defaults
    # till everything is configured properly
    def __init__(
            self,
            logger_label: str,
            resource_router: str,
            resource_base_dir: str = BASE_DIR,
            server_url: str = SERVER_URL,
            log_level: str = "INFO"
    ):

        # Logger label of this manager - passed from the child class
        self.log = logging.getLogger(logger_label)
        self.log.setLevel(logging.getLevelName(log_level))

        # Server URL
        self._server_url = server_url
        # Base directory for all resource managers
        self._resource_base_dir = resource_base_dir
        # Routing key of this manager - passed from the child class
        self._resource_router = resource_router

        # Base directory of this manager - BASE_DIR/resource_router
        self._resource_dir = join(self._resource_base_dir, self._resource_router)
        # self._resource_dir = resource_dir

        log_msg = f"{self._resource_router}s base directory: {self._resource_dir}"
        if not exists(self._resource_dir):
            Path(self._resource_dir).mkdir(parents=True, exist_ok=True)
            self.log.info(f"Created non-existing {log_msg}")
        else:
            self.log.info(f"Using the existing {log_msg}")

    def get_all_resources(self, local: bool) -> List[Tuple[str, str]]:
        resources = []
        for res in scandir(self._resource_dir):
            if res.is_dir():
                if local:
                    resources.append((str(res.name), res))
                else:
                    url = self._to_resource(res.name, local=False)
                    resources.append((str(res.name), url))
        return resources

    def get_resource(self, resource_id: str, local: bool) -> Union[str, None]:
        """
        Returns the local path of the dir or
        the URL of the `resource_id`
        """
        res_path = self._has_dir(resource_id)
        if res_path:
            if local:
                return res_path
            url = self._to_resource(resource_id, local=False)
            return url
        return None

    def get_resource_job(self, resource_id: str, job_id: str, local: bool) -> Union[str, None]:
        # Wrapper, in case the underlying
        # implementation has to change
        return self._to_resource_job(resource_id, job_id, local)

    def get_resource_file(self, resource_id: str, file_ext=None) -> Union[str, None]:
        # Wrapper, in case the underlying
        # implementation has to change
        return self._has_file(resource_id, file_ext=file_ext)

    def _has_dir(self, resource_id: str) -> Union[str, None]:
        """
        Returns the local path of the dir
        identified with `resource_id` or None
        """
        resource_dir = self._to_resource(resource_id, local=True)
        if exists(resource_dir) and isdir(resource_dir):
            return resource_dir
        return None

    def _has_file(self, resource_id: str, file_ext=None) -> Union[str, None]:
        """
        Returns the local path of the file identified
        with `resource_id` or None
        """
        resource_dir = self._to_resource(resource_id, local=True)
        for file in listdir(resource_dir):
            if file_ext and file.endswith(file_ext):
                return join(resource_dir, file)
        return None

    def _to_resource(self, resource_id: str, local: bool) -> str:
        """
        Returns the built local path or URL of the
        `resource_id` without any checks
        """
        if local:
            return join(self._resource_base_dir, self._resource_router, resource_id)
        return join(self._server_url, self._resource_router, resource_id)

    def _to_resource_job(self, resource_id: str, job_id: str, local: bool) -> Union[str, None]:
        resource_base = self._to_resource(resource_id, local)
        if self._has_dir(resource_id):
            return join(resource_base, job_id)
        return None

    def _create_resource_dir(self, resource_id: str = None) -> Tuple[str, str]:
        if resource_id is None:
            resource_id = generate_id()
        resource_dir = self._to_resource(resource_id, local=True)
        if exists(resource_dir):
            self.log.error("Cannot create: {resource_id}. Resource already exists!")
            # TODO: Raise an Exception here
        mkdir(resource_dir)
        return resource_id, resource_dir

    def _delete_resource_dir(self, resource_id: str) -> Tuple[str, str]:
        resource_dir = self._to_resource(resource_id, local=True)
        if isdir(resource_dir):
            shutil.rmtree(resource_dir, ignore_errors=True)
        return resource_id, resource_dir

    # TODO: Getting rid of the duplication seems
    #  trickier than expected implementing a single method is harder
    @staticmethod
    async def _receive_resource(file, resource_dest):
        async with aiofiles.open(resource_dest, "wb") as fpt:
            content = await file.read(1024)
            while content:
                await fpt.write(content)
                content = await file.read(1024)

    @staticmethod
    async def _receive_resource2(file_path, resource_dest):
        with open(file_path, "rb") as fin:
            with open(resource_dest, "wb") as fout:
                content = fin.read(1024)
                while content:
                    fout.write(content)
                    content = fin.read(1024)
