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

    "PARAMS_KEY_DOCKER_PWD",
    "PARAMS_KEY_DOCKER_VOLUME",
    "PARAMS_KEY_DOCKER_MODELS",
    "PARAMS_KEY_DOCKER_IMAGE",
    "PARAMS_KEY_DOCKER_COMMAND",
    "PARAMS_KEY_INPUT_FILE_GRP",
    "PARAMS_KEY_METS_PATH",
    "PARAMS_KEY_WORKSPACE_PATH",

    "PH_DOCKER_COMMAND",
    "PH_DIR_IN",
    "PH_DIR_OUT",
    "PH_METS_FILE",

    "REPR_DOCKER_COMMAND",
    "REPR_DOCKER_IMAGE",
    "REPR_DOCKER_MODELS",
    "REPR_DOCKER_MODELS_DIR",
    "REPR_DOCKER_PWD",
    "REPR_DOCKER_VOLUME",
    "REPR_INPUT_FILE_GRP",
    "REPR_METS_PATH",
    "REPR_MODELS_PATH",
    "REPR_WORKSPACE_PATH",

    "SPACES"
]

OCRD_ALL_JSON_FILE = resource_filename(__name__, 'ocrd_all_tool.json')
with open(OCRD_ALL_JSON_FILE) as f:
    OCRD_ALL_JSON = load(f)

OTON_LOG_LEVEL = environ.get("OTON_LOG_LEVEL", "INFO")
OTON_LOG_FORMAT = '%(asctime)s %(levelname)s %(name)s:%(funcName)s: %(lineno)s: %(message)s'

# Parameter keys
PARAMS_KEY_DOCKER_COMMAND: str = 'params.docker_command'
PARAMS_KEY_DOCKER_IMAGE: str = 'params.docker_image'
PARAMS_KEY_DOCKER_PWD: str = 'params.docker_pwd'
PARAMS_KEY_DOCKER_VOLUME: str = 'params.docker_volume'
PARAMS_KEY_DOCKER_MODELS: str = 'params.docker_models'
PARAMS_KEY_DOCKER_MODELS_DIR: str = 'params.docker_models_dir'
PARAMS_KEY_METS_PATH: str = 'params.mets_path'
PARAMS_KEY_INPUT_FILE_GRP: str = 'params.input_file_grp'
PARAMS_KEY_MODELS_PATH: str = 'params.models_path'
PARAMS_KEY_WORKSPACE_PATH: str = 'params.workspace_path'


def __build_docker_command():
    docker_command = 'docker run --rm'
    docker_command += f' -u \\$(id -u)'
    docker_command += f' -v ${PARAMS_KEY_DOCKER_VOLUME}'
    docker_command += f' -v ${PARAMS_KEY_DOCKER_MODELS}'
    docker_command += f' -w ${PARAMS_KEY_DOCKER_PWD}'
    docker_command += f' -- ${PARAMS_KEY_DOCKER_IMAGE}'
    return docker_command


def __build_repr(parameter, value):
    return f'{parameter} = "{value}"'


# Parameters - file representation
REPR_DOCKER_COMMAND: str = __build_repr(PARAMS_KEY_DOCKER_COMMAND, __build_docker_command())
REPR_DOCKER_IMAGE: str = __build_repr(PARAMS_KEY_DOCKER_IMAGE, "null")
REPR_DOCKER_MODELS: str = __build_repr(PARAMS_KEY_DOCKER_MODELS,
                                       f'${PARAMS_KEY_MODELS_PATH}:${PARAMS_KEY_DOCKER_MODELS_DIR}')
REPR_DOCKER_MODELS_DIR: str = __build_repr(PARAMS_KEY_DOCKER_MODELS_DIR, "null")
REPR_DOCKER_PWD: str = __build_repr(PARAMS_KEY_DOCKER_PWD, "null")
REPR_DOCKER_VOLUME: str = __build_repr(PARAMS_KEY_DOCKER_VOLUME,
                                       f'${PARAMS_KEY_WORKSPACE_PATH}:${PARAMS_KEY_DOCKER_PWD}')
REPR_METS_PATH: str = __build_repr(PARAMS_KEY_METS_PATH, "null")
REPR_INPUT_FILE_GRP: str = __build_repr(PARAMS_KEY_INPUT_FILE_GRP, "null")
REPR_MODELS_PATH: str = __build_repr(PARAMS_KEY_MODELS_PATH, "null")
REPR_WORKSPACE_PATH: str = __build_repr(PARAMS_KEY_WORKSPACE_PATH, "null")

DIR_IN: str = 'input_file_grp'
DIR_OUT: str = 'output_file_grp'
METS_FILE: str = 'mets_file'

# Placeholders
BS: str = '{}'
PH_DOCKER_COMMAND: str = f'${BS[0]}{PARAMS_KEY_DOCKER_COMMAND}{BS[1]}'
PH_DIR_IN: str = f'${BS[0]}{DIR_IN}{BS[1]}'
PH_DIR_OUT: str = f'${BS[0]}{DIR_OUT}{BS[1]}'
PH_METS_FILE: str = f'${BS[0]}{METS_FILE}{BS[1]}'
SPACES = '    '
