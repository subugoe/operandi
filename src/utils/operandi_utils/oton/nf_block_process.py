import logging
from operandi_utils.oton.validator import ProcessorCallArguments
from operandi_utils.oton.constants import OTON_LOG_LEVEL, OTON_LOG_FORMAT, PH_DIR_IN, PH_DIR_OUT, PH_METS_FILE, PH_DOCKER_COMMAND, SPACES


class NextflowBlockProcess:
    def __init__(self, processor_call_arguments: ProcessorCallArguments, index_pos: int, dockerized: bool = False):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.getLevelName(OTON_LOG_LEVEL))
        logging.basicConfig(format=OTON_LOG_FORMAT)

        self.dockerized = dockerized
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
        self.directives = []
        self.input_params = []
        self.output_params = []

    def file_representation(self):
        representation = f'process {self.nf_process_name}' + ' {\n'

        for directive in self.directives:
            representation += f'{SPACES}{directive}\n'
        representation += '\n'

        representation += f'{SPACES}input:\n'
        for input_param in self.input_params:
            representation += f'{SPACES}{SPACES}{input_param}\n'
        representation += '\n'

        representation += f'{SPACES}output:\n'
        for output_param in self.output_params:
            representation += f'{SPACES}{SPACES}{output_param}\n'
        representation += '\n'

        representation += f'{SPACES}script:\n'
        representation += f'{SPACES}{SPACES}"""\n'
        if self.dockerized:
            representation += f'{SPACES}{SPACES}{PH_DOCKER_COMMAND} {self.ocrd_command_bash}\n'
        else:
            representation += f'{SPACES}{SPACES}{self.ocrd_command_bash}\n'
        representation += f'{SPACES}{SPACES}"""\n'

        representation += '}\n'

        self.logger.debug(f"\n{representation}")
        return representation

    def add_directive(self, directive: str):
        self.directives.append(directive)

    def add_input_param(self, parameter: str):
        self.input_params.append(parameter)

    def add_output_param(self, parameter: str):
        self.output_params.append(parameter)
