from json import dumps as json_dumps, loads as json_loads
from logging import Logger
from os.path import exists, isfile
from typing import Dict
from .constants import VD18_DATA_JSON, VD18_METS_EXT, VD18_URL


def build_vd18_remote_url(logger: Logger, vd18_ppn_id: str) -> str:
    remote_url = f"{VD18_URL}{vd18_ppn_id}{VD18_METS_EXT}"
    logger.info(f"Building the remote url of {vd18_ppn_id}: {remote_url}")
    return remote_url


def check_file_existence(logger: Logger, file_path: str):
    if not exists(file_path):
        msg = f"Path does not exist: {file_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)
    if not isfile(file_path):
        msg = f"Path is not a file: {file_path}"
        logger.error(msg)
        raise FileNotFoundError(msg)


def load_vd18_data(logger: Logger, json_path: str = VD18_DATA_JSON) -> Dict:
    vd18_data: Dict = {}
    try:
        check_file_existence(logger, json_path)
    except FileNotFoundError:
        logger.warning("VD18 data json file does not exist, returning an empty dict")
        return vd18_data
    with open(json_path, 'r', encoding='utf-8') as fptr:
        vd18_data = json_loads(fptr.read())
    return vd18_data


def save_vd18_data(logger: Logger, vd18_data: Dict, json_path: str = VD18_DATA_JSON):
    with open(json_path, 'w') as fptr:
        fptr.write(json_dumps(vd18_data, indent=4))
    logger.info(f"VD18 data json was saved to: {json_path}")
