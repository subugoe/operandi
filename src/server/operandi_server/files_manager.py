import aiofiles
from io import DEFAULT_BUFFER_SIZE
from os import environ, listdir, scandir
from os.path import isdir, isfile, join
from pathlib import Path
from shutil import rmtree
from typing import List, Tuple
from operandi_utils import generate_id


def abs_resource_router_dir_path(resource_router: str) -> str:
    server_base_dir = environ.get("OPERANDI_SERVER_BASE_DIR", None)
    if not server_base_dir:
        raise ValueError("Environment variable not set: OPERANDI_SERVER_BASE_DIR")
    return join(server_base_dir, resource_router)


def abs_resource_dir_path(resource_router: str, resource_id: str) -> str:
    return join(abs_resource_router_dir_path(resource_router), resource_id)


def abs_resource_url(resource_router: str, resource_id: str) -> str:
    server_base_live_url = environ.get("OPERANDI_SERVER_URL_LIVE", None)
    if not server_base_live_url:
        raise ValueError("Environment variable not set: OPERANDI_SERVER_URL_LIVE")
    return join(server_base_live_url, resource_router, resource_id)


def create_resource_base_dir(resource_router: str) -> str:
    resource_abs_path = abs_resource_router_dir_path(resource_router)
    Path(resource_abs_path).mkdir(mode=0o777, parents=True, exist_ok=True)
    return resource_abs_path


def create_resource_dir(resource_router: str, resource_id: str = None, exists_ok=False) -> Tuple[str, str]:
    if resource_id is None:
        resource_id = generate_id()
    resource_dir = abs_resource_dir_path(resource_router, resource_id)
    if isdir(resource_dir):
        if not exists_ok:
            raise FileExistsError(f"Failed to create resource dir, already exists: {resource_dir}")
    Path(resource_dir).mkdir(mode=0o777, parents=True, exist_ok=True)
    return resource_id, resource_dir


def delete_resource_dir(resource_router: str, resource_id: str) -> Tuple[str, str]:
    resource_dir = abs_resource_dir_path(resource_router, resource_id)
    if not isdir(resource_dir):
        raise FileNotFoundError(f"Resource dir not found: {resource_dir}")
    rmtree(resource_dir, ignore_errors=True)
    return resource_id, resource_dir


def get_all_resources_local(resource_router: str) -> List[Tuple[str, str]]:
    resources = []
    router_dir = abs_resource_router_dir_path(resource_router)
    for res in scandir(router_dir):
        if res.is_dir():
            resource_id = str(res.name)
            resource_dir = str(res)
            resources.append((resource_id, resource_dir))
    return resources


def get_all_resources_url(resource_router: str) -> List[Tuple[str, str]]:
    resources = []
    router_dir = abs_resource_router_dir_path(resource_router)
    for res in scandir(router_dir):
        if res.is_dir():
            resource_id = str(res.name)
            url = abs_resource_url(resource_router, resource_id)
            resources.append((resource_id, url))
    return resources


def get_resource_local(resource_router: str, resource_id: str) -> str:
    resource_dir = abs_resource_dir_path(resource_router, resource_id)
    if not isdir(resource_dir):
        raise FileNotFoundError(f"Resource dir not found: {resource_dir}")
    return resource_dir


def get_resource_url(resource_router: str, resource_id: str) -> str:
    resource_dir = abs_resource_dir_path(resource_router, resource_id)
    if not isdir(resource_dir):
        raise FileNotFoundError(f"Resource dir not found: {resource_dir}")
    return abs_resource_url(resource_router, resource_id)


def get_resource_file(resource_router: str, resource_id: str, file_ext=None) -> str:
    resource_dir = abs_resource_dir_path(resource_router, resource_id)
    if not isdir(resource_dir):
        raise FileNotFoundError(f"Resource dir not found: {resource_dir}")
    for file in listdir(resource_dir):
        if isfile(file):
            if file_ext and file.endswith(file_ext):
                return join(resource_dir, file)
    raise FileNotFoundError(f"Resource file with ending '{file_ext}' not found in: {resource_dir}")


async def receive_resource(file, resource_dst, chunk_size: int = DEFAULT_BUFFER_SIZE):
    async with aiofiles.open(file=resource_dst, mode="wb") as fpt:
        content = await file.read(chunk_size)
        while content:
            await fpt.write(content)
            content = await file.read(chunk_size)
