import json
import logging
from shlex import split as shlex_split
from typing import List, Optional, Tuple

from ocrd_utils import parse_json_string_or_file, set_json_key_value_overrides
from operandi_utils.oton.constants import OCRD_ALL_JSON, OTON_LOG_LEVEL


# This class is based on ocrd.task_sequence.ProcessorTask
class ProcessorCallArguments:
    def __init__(
        self,
        executable: str,
        input_file_grps: Optional[str] = None,
        output_file_grps: Optional[str] = None,
        parameters: Optional[dict] = None,
        mets_file_path: str = "./mets.xml"
    ):
        if not executable:
            raise ValueError(f"Missing executable name")
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.getLevelName(OTON_LOG_LEVEL))

        self.executable = f'ocrd-{executable}'
        self.mets_file_path = mets_file_path
        self.input_file_grps = input_file_grps
        self.output_file_grps = output_file_grps
        self.parameters = parameters if parameters else {}
        self.ocrd_tool_json = OCRD_ALL_JSON.get(self.executable, None)

    def __str__(self):
        str_repr = f"{self.executable} -m {self.mets_file_path} -I {self.input_file_grps} -O {self.output_file_grps}"
        if self.parameters:
            str_repr += f" -p '{json.dumps(self.parameters)}'"
        return str_repr

    def self_validate(self):
        if not self.ocrd_tool_json:
            self.logger.error(f"Ocrd tool JSON of '{self.executable}' not found!")
            raise ValueError(f"Ocrd tool JSON of '{self.executable}' not found!")
        if not self.input_file_grps:
            self.logger.error(f"Processor '{self.executable}' requires 'input_file_grp' but none was provided.")
            raise ValueError(f"Processor '{self.executable}' requires 'input_file_grp' but none was provided.")
        if 'output_file_grp' in self.ocrd_tool_json and not self.output_file_grps:
            self.logger.error(f"Processor '{self.executable}' requires 'output_file_grp' but none was provided.")
            raise ValueError(f"Processor '{self.executable}' requires 'output_file_grp' but none was provided.")


class OCRDParser:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.getLevelName(OTON_LOG_LEVEL))

    def parse_arguments(self, processor_arguments) -> ProcessorCallArguments:
        tokens = shlex_split(processor_arguments)
        processor_call_arguments = ProcessorCallArguments(executable=f"{tokens.pop(0)}")
        self.logger.debug(f"Parsing arguments of processor: {processor_call_arguments.executable}")
        parameters = {}
        while tokens:
            self.logger.debug(f"Current token: {tokens[0]}")
            if tokens[0] == '-I':
                input_file_grps = []
                for grp in tokens[1].split(','):
                    input_file_grps.append(grp)
                processor_call_arguments.input_file_grps = ','.join(input_file_grps)
                self.logger.debug(f"Parsed input file groups: {processor_call_arguments.input_file_grps}")
                tokens = tokens[2:]
            elif tokens[0] == '-O':
                output_file_grps = []
                for grp in tokens[1].split(','):
                    output_file_grps.append(grp)
                processor_call_arguments.output_file_grps = ','.join(output_file_grps)
                self.logger.debug(f"Parsed output file groups: {processor_call_arguments.output_file_grps}")
                tokens = tokens[2:]
            elif tokens[0] == '-p':
                parameters = {**parameters, **parse_json_string_or_file(tokens[1])}
                processor_call_arguments.parameters = parameters
                self.logger.debug(f"Parsed -p parameters: {processor_call_arguments.parameters}")
                tokens = tokens[2:]
            elif tokens[0] == '-P':
                set_json_key_value_overrides(parameters, tokens[1:3])
                processor_call_arguments.parameters = parameters
                self.logger.debug(f"Parsed -P parameter: {processor_call_arguments.parameters}")
                tokens = tokens[3:]
            elif tokens[0] == '-m':
                processor_call_arguments.mets_file_path = tokens[1]
                self.logger.debug(f"Parsed mets file path: {processor_call_arguments.mets_file_path}")
                tokens = tokens[2:]
            else:
                message = f"Failed parsing processor arguments: {processor_arguments} with tokens remaining: {tokens}"
                self.logger.error(message)
                raise ValueError(message)
        processor_call_arguments.self_validate()
        self.logger.info(f"Successfully validated parameters of processor: {processor_call_arguments.executable}")
        return processor_call_arguments

    def purify_line(self, line: str) -> str:
        """
        A method that gets an ocrd processor call line and purifies it by removing unnecessary whitespaces and symbols.
        E.g.:
        input: "cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN" \
        output: cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN
        """
        self.logger.debug(f"Line to purify: {line}")
        # remove whitespaces
        cleaned_line = line.strip()
        # remove the backslash at the end
        if cleaned_line.endswith('\\'):
            cleaned_line = cleaned_line[:-1].strip()
        # remove the quotation marks at the start and end
        if cleaned_line.startswith('"') and cleaned_line.endswith('"'):
            cleaned_line = cleaned_line[1:-1]
        self.logger.debug(f"Cleaned line: {cleaned_line}")
        return cleaned_line

    def read_from_file(self, input_file: str) -> Tuple[str, List[str]]:
        file_lines = []
        self.logger.info(f"Trying to read lines to parse from input file: {input_file}")
        with open(input_file, mode='r', encoding='utf-8') as ocrd_file:
            line_counter = 1
            for line in ocrd_file:
                purified_line = self.purify_line(line)
                if len(purified_line) > 0:
                    self.logger.info(f"Appending purified line {line_counter}: {purified_line}")
                    file_lines.append(purified_line)
                else:
                    self.logger.info(f"0 sized line {line_counter} spotted, skipping")
                line_counter += 1
        ocrd_process_command = file_lines[0]
        processor_tasks = file_lines[1:]
        return ocrd_process_command, processor_tasks
