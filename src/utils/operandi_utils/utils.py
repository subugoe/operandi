from clint.textui import progress
from functools import wraps
from os import makedirs, sep
from os.path import basename, dirname, exists
from pika import URLParameters
from pymongo import uri_parser as mongo_uri_parser
from re import match as re_match
from requests import get, post
from requests.exceptions import RequestException
from shutil import make_archive, move, unpack_archive
from typing import Dict


# Based on:
# https://gist.github.com/phizaz/20c36c6734878c6ec053245a477572ec
def call_sync(func):
    import asyncio

    @wraps(func)
    def func_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if asyncio.iscoroutine(result):
            return asyncio.get_event_loop().run_until_complete(result)
        return result
    return func_wrapper


def download_mets_file(mets_url, ocrd_workspace_dir):
    if not exists(ocrd_workspace_dir):
        makedirs(ocrd_workspace_dir)
    filename = f"{ocrd_workspace_dir}/mets.xml"

    try:
        response = get(mets_url, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as file:
                # Unfortunately the responses from GDZ does not
                # contain content-length information in the response
                # header. The line below is a "bad" hack to find the
                # size of the mets file
                length = response.content.__sizeof__() - 33
                size = (length / 512) + 1
                # TODO: The progress bar is not working as expected
                # TODO: Consider to remove it completely
                for chunk in progress.bar(response.iter_content(chunk_size=512), expected_size=size):
                    if chunk:
                        file.write(chunk)
                        file.flush()
            return True
    except RequestException as e:
        return False


def is_url_responsive(url: str) -> bool:
    try:
        response = get(url, stream=True)
        if response.status_code // 100 == 2:
            return True
    except Exception as e:
        return False


def make_zip_archive(source, destination):
    base = basename(destination)
    name = base.split('.')[0]
    zip_format = base.split('.')[1]
    archive_from = dirname(source)
    archive_to = basename(source.strip(sep))
    make_archive(name, zip_format, archive_from, archive_to)
    move(f'{name}.{zip_format}', destination)


def unpack_zip_archive(source, destination):
    unpack_archive(filename=source, extract_dir=destination)


# TODO: Conceptual implementation, not tested in any way yet
def send_bag_to_ola_hd(path_to_bag) -> str:
    # Ola-HD dev instance,
    # available only when connected to GOENET
    url = 'http://141.5.99.53/api/bag'
    files = {'file': open(path_to_bag, 'rb')}
    params = {'isGt': False}
    # The credentials here are already publicly available inside the ola-hd repo
    # Ignore docker warnings about exposed credentials
    ola_hd_response = post(url, files=files, data=params, auth=("admin", "JW24G.xR"))
    if ola_hd_response.status_code >= 400:
        ola_hd_response.raise_for_status()
    return ola_hd_response.json()['pid']


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
        'username': url_params.credentials.username,
        'password': url_params.credentials.password,
        'host': url_params.host,
        'port': url_params.port,
        'vhost': url_params.virtual_host
    }
    return parsed_data
