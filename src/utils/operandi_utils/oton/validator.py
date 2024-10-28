from copy import deepcopy
import logging
from os.path import exists, isfile
from typing import List

from ocrd_validators import ParameterValidator
from operandi_utils.oton.constants import OTON_LOG_LEVEL, OTON_LOG_FORMAT
from operandi_utils.oton.parser import OCRDParser, ProcessorCallArguments


__all__ = ["OCRDValidator"]

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName(OTON_LOG_LEVEL))
logging.basicConfig(format=OTON_LOG_FORMAT)

class OCRDValidator:
    def __init__(self):
        self.ocrd_process_command: str = ''
        self.processors: List[ProcessorCallArguments] = []

    def validate(self, input_file: str):
        self.validate_file_path(input_file)
        self.ocrd_process_command, processor_tasks = OCRDParser.read_from_file(input_file)

        print(f"OCRD_PROCESS: {self.ocrd_process_command}")
        self.validate_ocrd_process_command(self.ocrd_process_command)
        for task in processor_tasks:
            print(f"TASK: [{task}]")

        for processor_arguments in processor_tasks:
            processor_call_arguments: ProcessorCallArguments = OCRDParser.parse_arguments(processor_arguments)
            self.processors.append(processor_call_arguments)

        for processor in self.processors:
            print(f"ProcessorCore: [{processor}]")

        self.validate_all_processors(self.processors)

    @staticmethod
    def validate_file_path(filepath: str):
        if not exists(filepath):
            raise ValueError(f"{filepath} does not exist!")
        if not isfile(filepath):
            raise ValueError(f"{filepath} is not a readable file!")
        logger.debug(f"Input file path validated: {filepath}")

    @staticmethod
    def validate_all_processors(processors: List[ProcessorCallArguments]):
        prev_output_file_grps = []
        first_processor = processors[0]
        OCRDValidator().validate_processor_params(first_processor, overwrite_with_defaults=False)

        prev_output_file_grps += first_processor.output_file_grps.split(',')
        for processor in processors[1:]:
            OCRDValidator().validate_processor_params(processor, overwrite_with_defaults=False)
            for input_file_grp in processor.input_file_grps.split(','):
                if input_file_grp not in prev_output_file_grps:
                    # TODO: This is not ideal...
                    if "GT" not in input_file_grp:
                        if "OCR-D-OCR" not in input_file_grp:
                            raise ValueError(f"Input file group not produced by previous steps: {input_file_grp}")
            prev_output_file_grps += processor.output_file_grps.split(',')

    @staticmethod
    def validate_processor_params(processor_args: ProcessorCallArguments, overwrite_with_defaults=False):
        # The ParameterValidator overwrites the missing parameters with their defaults
        if not overwrite_with_defaults:
            backup_curr_params = deepcopy(processor_args.parameters)

        report = ParameterValidator(processor_args.ocrd_tool_json).validate(processor_args.parameters)
        if not report.is_valid:
            raise Exception(report.errors)

        # Remove the overwritten defaults to keep the produced NF executable file less populated
        # Note: The defaults, still get overwritten in run-time
        if not overwrite_with_defaults:
            processor_args.parameters = deepcopy(backup_curr_params)
        return report

    @staticmethod
    def validate_ocrd_process_command(line: str):
        expected = 'ocrd process'
        if line != expected:
            raise ValueError(f"Invalid first line. Expected: '{expected}', got: '{line}'")
        logger.info(f"Line 0 was validated successfully")
