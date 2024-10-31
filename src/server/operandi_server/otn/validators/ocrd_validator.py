from copy import deepcopy
import json
from typing import List, Optional
from shlex import split as shlex_split

from ocrd_validators import ParameterValidator
from ocrd_utils import parse_json_string_or_file, set_json_key_value_overrides

from ..constants import OCRD_ALL_JSON
from .validator_utils import (
    validate_file_path,
    validate_ocrd_process_command,
)
from ..utils import read_from_file


# This class is based on ocrd.task_sequence.ProcessorTask
class ProcessorCallArguments:
    def __init__(
        self,
        executable: str,
        input_file_grps: str,
        output_file_grps: Optional[str] = None,
        parameters: Optional[dict] = None,
        mets_file_path: str = ""
    ):
        if not executable:
            raise ValueError(f"Missing executable name")
        if not input_file_grps:
            raise ValueError(f"Missing input file group of '{executable}'")

        self.executable = f'ocrd-{executable}'
        self.mets_file_path = mets_file_path
        self.input_file_grps = input_file_grps
        self.output_file_grps = output_file_grps
        self.parameters = parameters

        self.ocrd_tool_json = OCRD_ALL_JSON.get(self.executable, None)
        if not self.ocrd_tool_json:
            raise ValueError(f"Ocrd tool JSON of '{self.executable}' not found!")
        if 'output_file_grp' in self.ocrd_tool_json and not self.output_file_grps:
            raise ValueError(f"Processor '{executable}' requires 'output_file_grp' but none was provided.")

    def __str__(self):
        str_repr = f"{self.executable}" \
                   f" -m {self.mets_file_path}" \
                   f" -I {self.input_file_grps}" \
                   f" -O {self.output_file_grps}"
        if self.parameters:
            str_repr += f" -p '{json.dumps(self.parameters)}'"
        return str_repr


def validate_processor_params(processor_args: ProcessorCallArguments, overwrite_with_defaults=False):
    # The ParameterValidator overwrites the missing parameters with their defaults
    backup_curr_params = deepcopy(processor_args.parameters)

    report = ParameterValidator(processor_args.ocrd_tool_json).validate(processor_args.parameters)
    if not report.is_valid:
        raise Exception(report.errors)

    # Remove the overwritten defaults to keep the produced NF executable file less populated
    # Note: The defaults, still get overwritten in run-time
    if not overwrite_with_defaults:
        processor_args.parameters = deepcopy(backup_curr_params)
    return report


def validate_all_processors(processors: List[ProcessorCallArguments]):
    prev_output_file_grps = []

    first_processor = processors[0]
    validate_processor_params(first_processor, overwrite_with_defaults=False)

    prev_output_file_grps += first_processor.output_file_grps.split(',')
    for processor in processors[1:]:
        validate_processor_params(processor, overwrite_with_defaults=False)
        for input_file_grp in processor.input_file_grps.split(','):
            if input_file_grp not in prev_output_file_grps:
                # TODO: This is not ideal...
                if "GT" not in input_file_grp:
                    if "OCR-D-OCR" not in input_file_grp:
                        raise ValueError(f"Input file group not produced by previous steps: {input_file_grp}")
        prev_output_file_grps += processor.output_file_grps.split(',')


def parse_arguments(processor_arguments) -> ProcessorCallArguments:
    tokens = shlex_split(processor_arguments)
    executable = f"{tokens.pop(0)}"
    input_file_grps = []
    output_file_grps = []
    parameters = {}
    while tokens:
        if tokens[0] == '-I':
            for grp in tokens[1].split(','):
                input_file_grps.append(grp)
            tokens = tokens[2:]
        elif tokens[0] == '-O':
            for grp in tokens[1].split(','):
                output_file_grps.append(grp)
            tokens = tokens[2:]
        elif tokens[0] == '-p':
            parameters = {**parameters, **parse_json_string_or_file(tokens[1])}
            tokens = tokens[2:]
        elif tokens[0] == '-P':
            set_json_key_value_overrides(parameters, tokens[1:3])
            tokens = tokens[3:]
        else:
            raise ValueError(f"Failed parsing processor arguments: {processor_arguments} "
                             f"with tokens remaining: {tokens}")
    input_file_grps = ','.join(input_file_grps)
    output_file_grps = ','.join(output_file_grps)
    return ProcessorCallArguments(executable, input_file_grps, output_file_grps, parameters)


class OCRDValidator:
    def __init__(self):
        self.ocrd_process_command: str = ''
        self.processors: List[ProcessorCallArguments] = []

    def validate(self, input_file: str):
        validate_file_path(input_file)
        self.ocrd_process_command, processor_tasks = read_from_file(input_file)

        print(f"OCRD_PROCESS: {self.ocrd_process_command}")
        for task in processor_tasks:
            print(f"TASK: [{task}]")

        validate_ocrd_process_command(self.ocrd_process_command)
        for processor_arguments in processor_tasks:
            processor_call_arguments: ProcessorCallArguments = parse_arguments(processor_arguments)
            self.processors.append(processor_call_arguments)

        for processor in self.processors:
            print(f"ProcessorCore: [{processor}]")

        validate_all_processors(self.processors)
