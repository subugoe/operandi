from functools import wraps
from io import DEFAULT_BUFFER_SIZE
from os import makedirs, sep
from os.path import basename, dirname, exists
from pathlib import Path
from pika import URLParameters
from pymongo import uri_parser as mongo_uri_parser
from re import match as re_match
from requests import get, post
from requests.exceptions import RequestException
from shutil import make_archive, move, unpack_archive
from uuid import uuid4

from ocrd_utils import initLogging

from .constants import OLA_HD_BAG_ENDPOINT, OLA_HD_USER, OLA_HD_PASSWORD


logging_initialized = False


def safe_init_logging() -> None:
    """
    wrapper around ocrd_utils.initLogging. It assures that ocrd_utils.initLogging is only called
    once. This function may be called multiple times
    """
    global logging_initialized
    if not logging_initialized:
        logging_initialized = True
        initLogging()


def call_sync(func):
    """
    Based on:
    https://gist.github.com/phizaz/20c36c6734878c6ec053245a477572ec
    """
    from asyncio import iscoroutine, get_event_loop

    @wraps(func)
    def func_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if iscoroutine(result):
            return get_event_loop().run_until_complete(result)
        return result
    return func_wrapper


def download_mets_file(
    mets_url, ocrd_workspace_dir, mets_basename: str = "mets.xml", chunk_size: int = DEFAULT_BUFFER_SIZE
) -> bool:
    try:
        response = get(mets_url, stream=True)
        if response.status_code != 200:
            return False
    except RequestException as request_error:
        return False
    except Exception as error:
        return False
    try:
        if not exists(ocrd_workspace_dir):
            makedirs(ocrd_workspace_dir)
        filename = Path(ocrd_workspace_dir, mets_basename)
        receive_file(response=response, download_path=filename, chunk_size=chunk_size, mode='wb')
    except FileExistsError as file_error:
        return False
    except OSError as os_error:
        return False
    except Exception as error:
        return False
    return True


def is_url_responsive(url: str) -> bool:
    try:
        response = get(url, stream=True)
        if response.status_code // 100 == 2:
            return True
    except RequestException as request_error:
        return False
    except Exception as error:
        return False


def get_nf_workflows_dir() -> Path:
    return Path(dirname(__file__), "hpc", "nextflow_workflows")


def generate_id(file_ext: str = None):
    generated_id = str(uuid4())
    if file_ext:
        generated_id += file_ext
    return generated_id


def receive_file(response, download_path, chunk_size: int = DEFAULT_BUFFER_SIZE, mode: str = "wb") -> None:
    with open(download_path, mode) as filePtr:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                filePtr.write(chunk)
                filePtr.flush()


def make_zip_archive(source, destination) -> None:
    base = basename(destination)
    name = base.split('.')[0]
    zip_format = base.split('.')[1]
    archive_from = dirname(source)
    archive_to = basename(source.strip(sep))
    make_archive(base_name=name, format=zip_format, root_dir=archive_from, base_dir=archive_to)
    move(src=f"{name}.{zip_format}", dst=destination)


def unpack_zip_archive(source, destination) -> None:
    unpack_archive(filename=source, extract_dir=destination)


# TODO: Conceptual implementation, not tested in any way yet
def send_bag_to_ola_hd(path_to_bag, json_pid_field: str = "pid") -> str:
    ola_hd_files = {"file": open(path_to_bag, "rb")}
    ola_hd_auth = (OLA_HD_USER, OLA_HD_PASSWORD)
    ola_hd_response = post(url=OLA_HD_BAG_ENDPOINT, files=ola_hd_files, data={"isGt": False}, auth=ola_hd_auth)
    if ola_hd_response.status_code >= 400:
        ola_hd_response.raise_for_status()
    return ola_hd_response.json()[json_pid_field]


def verify_database_uri(mongodb_address: str) -> str:
    try:
        # perform validation check
        mongo_uri_parser.parse_uri(uri=mongodb_address, validate=True)
    except Exception as error:
        raise ValueError(f"The MongoDB address '{mongodb_address}' is in wrong format, {error}")
    return mongodb_address


def verify_and_parse_mq_uri(rabbitmq_address: str):
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
