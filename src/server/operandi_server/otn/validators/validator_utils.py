import logging
from os.path import exists, isfile

from ..constants import (
    OTON_LOG_LEVEL,
    OTON_LOG_FORMAT
)

__all__ = [
    "validate_file_path",
    "validate_ocrd_process_command"
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName(OTON_LOG_LEVEL))
logging.basicConfig(format=OTON_LOG_FORMAT)


def validate_file_path(filepath: str):
    if not exists(filepath):
        raise ValueError(f"{filepath} does not exist!")
    if not isfile(filepath):
        raise ValueError(f"{filepath} is not a readable file!")
    logger.debug(f"Input file path validated: {filepath}")


def validate_ocrd_process_command(line: str):
    expected = 'ocrd process'
    if line != expected:
        raise ValueError(f"Invalid first line. Expected: '{expected}', got: '{line}'")
    logger.info(f"Line 0 was validated successfully")
