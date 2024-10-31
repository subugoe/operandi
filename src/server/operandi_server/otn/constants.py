# Added from https://github.com/MehmedGIT/OtoN_Converter/tree/master
from json import load
from os import environ
from pkg_resources import resource_filename


__all__ = [
    "DEFAULT_IN_FILE",
    "DEFAULT_OUT_FILE",
    "OCRD_ALL_JSON",
    "OTON_LOG_LEVEL",
    "OTON_LOG_FORMAT",
]

DEFAULT_IN_FILE = resource_filename(__name__, 'assets/workflow1.txt')
DEFAULT_OUT_FILE = resource_filename(__name__, 'assets/nextflow1.nf')
OCRD_ALL_JSON_FILE = resource_filename(__name__, 'assets/ocrd_all_tool.json')
with open(OCRD_ALL_JSON_FILE) as f:
    OCRD_ALL_JSON = load(f)

OTON_LOG_LEVEL = environ.get("OTON_LOG_LEVEL", "INFO")
OTON_LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s:%(funcName)s: %(lineno)s: %(message)s'
