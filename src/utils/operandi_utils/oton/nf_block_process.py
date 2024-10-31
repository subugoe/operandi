import logging
from operandi_utils.oton.validator import ProcessorCallArguments
from operandi_utils.oton.constants import (
    OTON_LOG_LEVEL, PH_DIR_IN, PH_DIR_OUT, PH_METS_FILE, PH_ENV_WRAPPER, SPACES)


class NextflowBlockProcess:
    def __init__(self, processor_call_arguments: ProcessorCallArguments, index_pos: int, env_wrapper: bool = False):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.getLevelName(OTON_LOG_LEVEL))

        self.directives = {}
        self.input_params = {}
        self.output_params = {}

        self.env_wrapper = env_wrapper
        self.nf_process_name = processor_call_arguments.executable.replace('-', '_') + "_" + str(index_pos)
        self.repr_in_workflow = [
            self.nf_process_name,
            f'"{processor_call_arguments.input_file_grps}"',
            f'"{processor_call_arguments.output_file_grps}"'
        ]

        processor_call_arguments.input_file_grps = PH_DIR_IN
        processor_call_arguments.output_file_grps = PH_DIR_OUT
        processor_call_arguments.mets_file_path = PH_METS_FILE

        self.ocrd_command_bash = f'{processor_call_arguments}'

    def add_directive(self, directive: str, value: str):
        if directive in self.directives:
            raise ValueError(f"Directive '{directive}' already exists with value '{value}'")
        self.directives[directive] = value

    def add_parameter_input(self, parameter: str, parameter_type: str):
        if parameter in self.input_params:
            raise ValueError(f"Input parameter '{parameter}' already exists with type '{parameter_type}'")
        self.input_params[parameter] = parameter_type

    def add_parameter_output(self, parameter: str, parameter_type: str):
        if parameter in self.output_params:
            raise ValueError(f"Output parameter '{parameter}' already exists with type '{parameter_type}'")
        self.output_params[parameter] = parameter_type

    def dump_directives(self) -> str:
        dump = ''
        for key, value in self.directives.items():
            dump += f'{SPACES}{key} {value}\n'
        dump += '\n'
        return dump

    def dump_parameters_input(self) -> str:
        dump = ''
        dump += f'{SPACES}input:\n'
        for key, value in self.input_params.items():
            dump += f'{SPACES}{SPACES}{value} {key}\n'
        dump += '\n'
        return dump

    def dump_parameters_output(self) -> str:
        dump = ''
        dump += f'{SPACES}output:\n'
        for key, value in self.output_params.items():
            dump += f'{SPACES}{SPACES}{value} {key}\n'
        dump += '\n'
        return dump

    def dump_script(self) -> str:
        dump = ''
        dump += f'{SPACES}script:\n'
        dump += f'{SPACES}{SPACES}"""\n'
        dump += f'{SPACES}{SPACES}'
        if self.env_wrapper:
            dump += f'{PH_ENV_WRAPPER} '
        dump += f'{self.ocrd_command_bash}\n'
        dump += f'{SPACES}{SPACES}"""\n'
        return dump

    def file_representation(self):
        representation = f'process {self.nf_process_name}'
        representation += ' {\n'
        representation += self.dump_directives()
        representation += self.dump_parameters_input()
        representation += self.dump_parameters_output()
        representation += self.dump_script()
        representation += '}\n'
        self.logger.debug(f"\n{representation}")
        return representation
