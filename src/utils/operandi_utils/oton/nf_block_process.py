from logging import getLevelName, getLogger
from operandi_utils.oton.ocrd_validator import ProcessorCallArguments
from operandi_utils.oton.constants import BS, OTON_LOG_LEVEL, PARAMS_KEY_ENV_WRAPPER_CMD_STEP, SPACES


class NextflowBlockProcess:
    def __init__(
        self, processor_call_arguments: ProcessorCallArguments,
        index_pos: int,
        with_mets_server: bool,
        env_wrapper: bool = False
    ):
        self.logger = getLogger(__name__)
        self.logger.setLevel(getLevelName(OTON_LOG_LEVEL))
        self.index_pos = str(index_pos)

        self.processor_call_arguments: ProcessorCallArguments = processor_call_arguments
        self.env_wrapper: bool = env_wrapper
        self.nf_process_name: str = processor_call_arguments.executable.replace('-', '_') + f"_{self.index_pos}"
        self.directives = {}
        self.input_params = {}
        self.output_params = {}
        self.script = ""
        self.ocrd_command_bash = processor_call_arguments.dump_bash_form()
        self.ocrd_command_bash_placeholders = processor_call_arguments.dump_bash_form_with_phs(with_mets_server)

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
        for key, value in self.input_params.items():
            dump += f'{SPACES}{SPACES}{value} {key}\n'
        dump += '\n'
        return dump

    def dump_parameters_output(self) -> str:
        dump = ''
        for key, value in self.output_params.items():
            dump += f'{SPACES}{SPACES}{value} {key}\n'
        dump += '\n'
        return dump

    def dump_script(self, local_script: bool = False) -> str:
        if local_script:
            return self.script
        dump = ''
        dump += f'{SPACES}{SPACES}"""\n'
        dump += f'{SPACES}{SPACES}'
        if self.env_wrapper:
            dump += f'${BS[0]}{PARAMS_KEY_ENV_WRAPPER_CMD_STEP}{self.index_pos}{BS[1]} '
        dump += f'{self.ocrd_command_bash_placeholders}\n'
        dump += f'{SPACES}{SPACES}"""\n'
        return dump

    def file_representation(self, local_script: bool = False):
        representation = f'process {self.nf_process_name}'
        representation += ' {\n'
        representation += self.dump_directives()
        representation += f'{SPACES}input:\n{self.dump_parameters_input()}'
        if len(self.output_params) > 0:
            representation += f'{SPACES}output:\n{self.dump_parameters_output()}'
        representation += f'{SPACES}script:\n{self.dump_script(local_script=local_script)}'
        representation += '}\n'
        self.logger.debug(f"\n{representation}")
        return representation
