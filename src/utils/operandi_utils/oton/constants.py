from json import load
from os import environ
from pkg_resources import resource_filename


__all__ = [
    "DIR_IN",
    "DIR_OUT",
    "METS_FILE",

    "OCRD_ALL_JSON",
    "OTON_LOG_LEVEL",
    "OTON_LOG_FORMAT",

    "PARAMS_KEY_INPUT_FILE_GRP",
    "PARAMS_KEY_METS_PATH",

    "PH_ENV_WRAPPER",
    "PH_DIR_IN",
    "PH_DIR_OUT",
    "PH_METS_FILE",

    "REPR_ENV_WRAPPER",
    "REPR_INPUT_FILE_GRP",
    "REPR_METS_PATH",
    "REPR_WORKSPACE_DIR",
    "SPACES"
]

OCRD_ALL_JSON_FILE = resource_filename(__name__, 'ocrd_all_tool.json')
with open(OCRD_ALL_JSON_FILE) as f:
    OCRD_ALL_JSON = load(f)

OTON_LOG_LEVEL = environ.get("OTON_LOG_LEVEL", "INFO")
OTON_LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s:%(funcName)s: %(lineno)s: %(message)s'

PARAMS_KEY_INPUT_FILE_GRP: str = 'params.input_file_group'
PARAMS_KEY_METS_PATH: str = 'params.mets_path'
PARAMS_KEY_WORKSPACE_DIR: str = 'params.workspace_dir'
PARAMS_KEY_ENV_WRAPPER: str = 'params.env_wrapper'

REPR_INPUT_FILE_GRP: str = f"""{PARAMS_KEY_INPUT_FILE_GRP} = "null\""""
REPR_METS_PATH: str = f"""{PARAMS_KEY_METS_PATH} = "null\""""
REPR_WORKSPACE_DIR: str = f"""{PARAMS_KEY_WORKSPACE_DIR} = "null\""""
REPR_ENV_WRAPPER: str = f"""{PARAMS_KEY_ENV_WRAPPER} = "null\""""

DIR_IN: str = 'input_file_group'
DIR_OUT: str = 'output_file_group'
METS_FILE: str = 'mets_file'

# Placeholders
BS: str = '{}'
PH_ENV_WRAPPER: str = f'${BS[0]}{PARAMS_KEY_ENV_WRAPPER}{BS[1]}'
PH_DIR_IN: str = f'${BS[0]}{DIR_IN}{BS[1]}'
PH_DIR_OUT: str = f'${BS[0]}{DIR_OUT}{BS[1]}'
PH_METS_FILE: str = f'${BS[0]}{METS_FILE}{BS[1]}'
SPACES = '    '
