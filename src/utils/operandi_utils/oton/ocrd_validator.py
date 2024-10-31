from copy import deepcopy
import logging
from os.path import exists, isfile
from typing import List

from ocrd_validators import ParameterValidator
from operandi_utils.oton.constants import OTON_LOG_LEVEL
from operandi_utils.oton.ocrd_parser import OCRDParser, ProcessorCallArguments


class OCRDValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.getLevelName(OTON_LOG_LEVEL))
        self.ocrd_parser = OCRDParser()

    def validate(self, input_file: str) -> List[ProcessorCallArguments]:
        self.validate_file_path(input_file)
        ocrd_process_command, processor_tasks = self.ocrd_parser.read_from_file(input_file)
        self.validate_ocrd_process_command(ocrd_process_command)

        list_processor_call_arguments: List[ProcessorCallArguments] = []
        for processor_arguments in processor_tasks:
            processor_call_arguments: ProcessorCallArguments = self.ocrd_parser.parse_arguments(processor_arguments)
            list_processor_call_arguments.append(processor_call_arguments)
        self.validate_all_processors(list_processor_call_arguments)
        return list_processor_call_arguments

    def validate_file_path(self, filepath: str):
        if not exists(filepath):
            self.logger.error(f"{filepath} does not exist!")
            raise ValueError(f"{filepath} does not exist!")
        if not isfile(filepath):
            self.logger.error(f"{filepath} is not a readable file!")
            raise ValueError(f"{filepath} is not a readable file!")
        self.logger.debug(f"Input file path validated: {filepath}")

    def validate_all_processors(self, processors: List[ProcessorCallArguments]):
        prev_output_file_grps = []
        first_processor = processors[0]
        self.logger.info(f"Validating parameters against json schema of processor: {first_processor.executable}")
        self.validate_processor_params(first_processor, overwrite_with_defaults=False)

        prev_output_file_grps += first_processor.output_file_grps.split(',')
        for processor in processors[1:]:
            self.logger.info(f"Validating parameters against json schema of processor: {first_processor.executable}")
            self.validate_processor_params(processor, overwrite_with_defaults=False)
            for input_file_grp in processor.input_file_grps.split(','):
                if input_file_grp not in prev_output_file_grps:
                    # TODO: This is not ideal...
                    if "GT" not in input_file_grp:
                        if "OCR-D-OCR" not in input_file_grp:
                            self.logger.error(f"Input file group not produced by previous steps: {input_file_grp}")
                            raise ValueError(f"Input file group not produced by previous steps: {input_file_grp}")
            prev_output_file_grps += processor.output_file_grps.split(',')

    def validate_processor_params(
        self, processor_args: ProcessorCallArguments, overwrite_with_defaults: bool = False):
        # The ParameterValidator overwrites the missing parameters with their defaults
        if not overwrite_with_defaults:
            self.logger.debug("Backing up the processor parameters with a deep copy")
            backup_curr_params = deepcopy(processor_args.parameters)

        report = ParameterValidator(processor_args.ocrd_tool_json).validate(processor_args.parameters)
        if not report.is_valid:
            self.logger.error(report.errors)
            raise Exception(report.errors)

        # Remove the overwritten defaults to keep the produced NF executable file less populated
        # Note: The defaults, still get overwritten in run-time
        if not overwrite_with_defaults:
            self.logger.debug("Restoring back the processor parameters from a deep copy")
            processor_args.parameters = deepcopy(backup_curr_params)
        return report

    def validate_ocrd_process_command(self, line: str):
        expected = 'ocrd process'
        if line != expected:
            self.logger.error(f"Invalid first line. Expected: '{expected}', got: '{line}'")
            raise ValueError(f"Invalid first line. Expected: '{expected}', got: '{line}'")
