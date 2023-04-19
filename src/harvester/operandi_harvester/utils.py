from os.path import exists, isfile
import requests

from .constants import (
    VD18_URL,
    VD18_METS_EXT,
)


def build_mets_url(mets_id: str) -> str:
    return f"{VD18_URL}{mets_id}{VD18_METS_EXT}"


def file_exists(file_path: str) -> bool:
    if exists(file_path) and isfile(file_path):
        return True
    return False


def is_url_responsive(url: str) -> bool:
    try:
        response = requests.get(url, stream=True)
        if response.status_code // 100 == 2:
            return True
    except requests.exceptions as e:
        return False


def parse_resource_id(json_response):
    return json_response['resource_url'].split("/")[-1]


def receive_file(response, download_path):
    with open(download_path, 'wb') as filePtr:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                filePtr.write(chunk)
