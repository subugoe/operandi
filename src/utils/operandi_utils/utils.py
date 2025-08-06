from datetime import datetime
from functools import wraps
from io import DEFAULT_BUFFER_SIZE
from os import sep
from os.path import basename, dirname
from pathlib import Path
from pika import URLParameters
from pymongo import uri_parser as mongo_uri_parser
from re import match as re_match
from requests import get as requests_get
from requests.exceptions import RequestException
from shutil import make_archive, move, unpack_archive
from uuid import uuid4
from typing import Any, Dict, Optional

from ocrd_utils import initLogging

logging_initialized = False

def safe_init_logging():
    """
    A wrapper around ocrd_utils.initLogging. It assures that ocrd_utils.initLogging is only called once.
    This function may be called multiple times without any side effects
    """
    global logging_initialized
    if not logging_initialized:
        logging_initialized = True
        initLogging()

def call_sync(func):
    """
    A wrapper to call async methods in a sync fashion.
    Based on: https://gist.github.com/phizaz/20c36c6734878c6ec053245a477572ec
    """
    from asyncio import iscoroutine, get_event_loop

    @wraps(func)
    def func_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if iscoroutine(result):
            return get_event_loop().run_until_complete(result)
        return result

    return func_wrapper

def create_db_query(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    hide_deleted: bool = True
) -> Dict[str, Any]:
    query: Dict[str, Any] = {"user_id": user_id}
    if start_date or end_date:
        query["datetime"] = {}
        if start_date:
            query["datetime"]["$gte"] = start_date
        if end_date:
            query["datetime"]["$lte"] = end_date
    if hide_deleted:
        query["deleted"] = False
    return query

def is_url_responsive(url: str) -> bool:
    try:
        response = requests_get(url, stream=True)
        if response.status_code // 100 == 2:
            return True
    except RequestException:
        return False
    except Exception:
        return False
    return False

def get_batch_scripts_dir() -> Path:
    return Path(dirname(__file__), "hpc", "batch_scripts")

def get_nf_wfs_dir() -> Path:
    return Path(dirname(__file__), "hpc", "nextflow_workflows")

def get_ocrd_process_wfs_dir() -> Path:
    return Path(dirname(__file__), "hpc", "ocrd_process_workflows")

def generate_id(file_ext: str = None):
    generated_id = str(uuid4())
    if file_ext:
        generated_id += file_ext
    return generated_id

def receive_file(response, download_path, chunk_size: int = DEFAULT_BUFFER_SIZE, mode: str = "wb"):
    with open(download_path, mode) as filePtr:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                filePtr.write(chunk)
                filePtr.flush()

def make_zip_archive(source, destination):
    base = basename(destination)
    name = base.split('.')[0]
    zip_format = base.split('.')[1]
    archive_from = dirname(source)
    archive_to = basename(str(source).strip(sep))
    make_archive(base_name=name, format=zip_format, root_dir=archive_from, base_dir=archive_to)
    move(src=f"{name}.{zip_format}", dst=destination)

def unpack_zip_archive(source, destination):
    unpack_archive(filename=source, extract_dir=destination)

def verify_database_uri(mongodb_address: str) -> str:
    try:
        # perform validation check
        mongo_uri_parser.parse_uri(uri=mongodb_address, validate=True)
    except Exception as error:
        raise ValueError(f"The MongoDB address '{mongodb_address}' is in wrong format, {error}")
    return mongodb_address

def verify_and_parse_mq_uri(rabbitmq_address: str) -> dict:
    """
    Check the full list of available parameters in the docs here:
    https://pika.readthedocs.io/en/stable/_modules/pika/connection.html#URLParameters
    """

    uri_pattern = r"^(?:([^:\/?#\s]+):\/{2})?(?:([^@\/?#\s]+)@)?([^\/?#\s]+)?(?:\/([^?#\s]*))?(?:[?]([^#\s]+))?\S*$"
    match = re_match(pattern=uri_pattern, string=rabbitmq_address)
    if not match:
        raise ValueError(f"The RabbitMQ server address is in wrong format: '{rabbitmq_address}'")
    url_params = URLParameters(rabbitmq_address)
    parsed_data = {
        "username": url_params.credentials.username,
        "password": url_params.credentials.password,
        "host": url_params.host,
        "port": url_params.port,
        "vhost": url_params.virtual_host
    }
    return parsed_data
