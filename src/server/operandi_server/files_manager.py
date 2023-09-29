import aiofiles
from os import listdir, scandir
from os.path import isdir, isfile, join
from pathlib import Path
import shutil
from typing import List, Tuple
from operandi_server.constants import BASE_DIR, SERVER_URL
from operandi_server.utils import generate_id


def create_resource_base_dir(resource_router: str) -> str:
    resource_abs_path = join(BASE_DIR, resource_router)
    if isdir(resource_abs_path):
        return resource_abs_path
    else:
        Path(resource_abs_path).mkdir(mode=0o777, parents=True, exist_ok=True)
        # If the resource base dir already exists, change the file mode
        Path(resource_abs_path).chmod(mode=0o777)
        return resource_abs_path


def create_resource_dir(resource_router: str, resource_id: str = None) -> Tuple[str, str]:
    if resource_id is None:
        resource_id = generate_id()
    resource_dir = join(BASE_DIR, resource_router, resource_id)
    if isdir(resource_dir):
        raise FileExistsError(f"Failed to create resource dir, already exists: {resource_dir}")
    Path(resource_dir).mkdir(mode=0o777)
    return resource_id, resource_dir


def delete_resource_dir(resource_router: str, resource_id: str) -> Tuple[str, str]:
    resource_dir = join(BASE_DIR, resource_router, resource_id)
    if isdir(resource_dir):
        shutil.rmtree(resource_dir, ignore_errors=True)
    else:
        raise FileNotFoundError(f"Resource dir not found: {resource_dir}")
    return resource_id, resource_dir


def get_all_resources_local(resource_router: str) -> List[Tuple[str, str]]:
    resources = []
    for res in scandir(join(BASE_DIR, resource_router)):
        if res.is_dir():
            resource_id = str(res.name)
            resource_dir = str(res)
            resources.append((resource_id, resource_dir))
    return resources


def get_all_resources_url(resource_router: str) -> List[Tuple[str, str]]:
    resources = []
    for res in scandir(join(BASE_DIR, resource_router)):
        if res.is_dir():
            resource_id = str(res.name)
            url = join(SERVER_URL, resource_router, resource_id)
            resources.append((resource_id, url))
    return resources


def get_resource_local(resource_router: str, resource_id: str) -> str:
    resource_dir = join(BASE_DIR, resource_router, resource_id)
    if isdir(resource_dir):
        return resource_dir
    raise FileNotFoundError(f"Resource dir not found: {resource_dir}")


def get_resource_url(resource_router: str, resource_id: str) -> str:
    resource_dir = join(BASE_DIR, resource_router, resource_id)
    if isdir(resource_dir):
        return join(SERVER_URL, resource_router, resource_id)
    raise FileNotFoundError(f"Resource dir not found: {resource_dir}")


def get_resource_file(resource_router: str, resource_id: str, file_ext=None) -> str:
    resource_dir = join(BASE_DIR, resource_router, resource_id)
    if not isdir(resource_dir):
        raise FileNotFoundError(f"Resource dir not found: {resource_dir}")
    for file in listdir(resource_dir):
        if isfile(file):
            if file_ext and file.endswith(file_ext):
                return join(resource_dir, file)
    raise FileNotFoundError(f"Resource file with ending '{file_ext}' not found in: {resource_dir}")


async def receive_resource(file, resource_dest):
    async with aiofiles.open(resource_dest, "wb") as fpt:
        content = await file.read(1024)
        while content:
            await fpt.write(content)
            content = await file.read(1024)
