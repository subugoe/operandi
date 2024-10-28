import logging
from typing import List, Tuple

from .constants import OTON_LOG_FORMAT, OTON_LOG_LEVEL

__all__ = ["read_from_file"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName(OTON_LOG_LEVEL))
logging.basicConfig(format=OTON_LOG_FORMAT)


def purify_line(line):
    # remove whitespaces
    cleaned_line = line.strip()
    # remove the backslash at the end
    if cleaned_line.endswith('\\'):
        cleaned_line = cleaned_line[:-1].strip()
    # remove the quotation marks at the start and end
    if cleaned_line.startswith('"') and cleaned_line.endswith('"'):
        cleaned_line = cleaned_line[1:-1]
    return cleaned_line


def read_from_file(input_file: str) -> Tuple[str, List[str]]:
    file_lines = []
    with open(input_file, mode='r', encoding='utf-8') as ocrd_file:
        for line in ocrd_file:
            purified_line = purify_line(line)
            if len(purified_line) > 0:
                file_lines.append(purified_line)

    ocrd_process_command = file_lines[0]
    processor_tasks = file_lines[1:]
    return ocrd_process_command, processor_tasks
