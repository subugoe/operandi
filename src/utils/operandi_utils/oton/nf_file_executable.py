from logging import getLevelName, getLogger
from typing import List

from operandi_utils.oton.ocrd_validator import ProcessorCallArguments
from operandi_utils.oton.constants import (
    BS, CONST_DIR_IN, CONST_DIR_OUT, CONST_PAGE_RANGE, CONST_METS_PATH, CONST_WORKSPACE_DIR,
    OTON_LOG_LEVEL,
    PARAMS_KEY_INPUT_FILE_GRP,
    PARAMS_KEY_METS_PATH,
    PARAMS_KEY_WORKSPACE_DIR,
    PARAMS_KEY_ENV_WRAPPER_CMD_CORE,
    PARAMS_KEY_ENV_WRAPPER_CMD_STEP,
    PARAMS_KEY_FORKS,
    PARAMS_KEY_CPUS_PER_FORK,
    PARAMS_KEY_RAM_PER_FORK,
    REPR_ENV_WRAPPER_CMD_CORE,
    REPR_INPUT_FILE_GRP,
    REPR_METS_PATH,
    REPR_METS_SOCKET_PATH,
    REPR_WORKSPACE_DIR,
    REPR_PAGES,
    REPR_CPUS,
    REPR_RAM,
    REPR_FORKS,
    REPR_FORKS_NULL,
    REPR_CPUS_PER_FORK,
    REPR_RAM_PER_FORK,
    SPACES,
    WORKFLOW_COMMENT
)
from operandi_utils.oton.nf_block_process import NextflowBlockProcess
from operandi_utils.oton.nf_block_workflow import NextflowBlockWorkflow


class NextflowFileExecutable:
    def __init__(self):
        self.logger = getLogger(__name__)
        self.logger.setLevel(getLevelName(OTON_LOG_LEVEL))

        self.supported_environments = ["local", "docker", "apptainer"]
        self.nf_lines_parameters: List[str] = []
        self.nf_process_split_range = None
        self.nf_process_merging_mets = None
        self.nf_blocks_process: List[NextflowBlockProcess] = []
        self.nf_blocks_workflow: List[NextflowBlockWorkflow] = []

    def build_parameters(self, environment: str, with_mets_server: bool):
        if environment not in self.supported_environments:
            raise ValueError(f"Invalid environment value: {environment}. Must be one of: {self.supported_environments}")

        self.nf_lines_parameters.append('nextflow.enable.dsl = 2')
        self.nf_lines_parameters.append('')
        self.nf_lines_parameters.append(REPR_INPUT_FILE_GRP)
        self.nf_lines_parameters.append(REPR_METS_PATH)
        self.nf_lines_parameters.append(REPR_WORKSPACE_DIR)
        self.nf_lines_parameters.append(REPR_PAGES)

        if with_mets_server:
            self.nf_lines_parameters.append(REPR_METS_SOCKET_PATH)

        if environment == "local":
            self.nf_lines_parameters.append(REPR_FORKS_NULL)
        if environment == "docker":
            self.nf_lines_parameters.append(REPR_FORKS_NULL)
            self.nf_lines_parameters.append(REPR_ENV_WRAPPER_CMD_CORE)
        if environment == "apptainer":
            self.nf_lines_parameters.append(REPR_CPUS)
            self.nf_lines_parameters.append(REPR_RAM)
            self.nf_lines_parameters.append(REPR_FORKS)
            self.nf_lines_parameters.append(REPR_CPUS_PER_FORK)
            self.nf_lines_parameters.append(REPR_RAM_PER_FORK)
            self.nf_lines_parameters.append(REPR_ENV_WRAPPER_CMD_CORE)

    # TODO: Refactor later
    def build_split_page_ranges_process(self, environment: str, with_mets_server: bool) -> NextflowBlockProcess:
        block = NextflowBlockProcess(ProcessorCallArguments(executable="split-page-ranges"), 0)
        block.nf_process_name = "split_page_ranges"
        block.ocrd_command_bash = ""
        block.ocrd_command_bash_placeholders = ""

        block.add_directive(directive='debug', value='true')
        block.add_directive(directive='maxForks', value=PARAMS_KEY_FORKS)
        if environment == "apptainer":
            block.add_directive(directive='cpus', value=PARAMS_KEY_CPUS_PER_FORK)
            block.add_directive(directive='memory', value=PARAMS_KEY_RAM_PER_FORK)

        block.add_parameter_input(parameter="range_multiplier", parameter_type="val")
        block.add_parameter_output(parameter="mets_file_chunk", parameter_type="env")
        block.add_parameter_output(parameter="current_range_pages", parameter_type="env")

        PH_RANGE_MULTIPLIER = '${range_multiplier}'
        bash_cmd_ocrd_ws = (
            f"ocrd workspace -d ${BS[0]}{PARAMS_KEY_WORKSPACE_DIR}{BS[1]} list-page -f comma-separated "
            f"-D ${BS[0]}{PARAMS_KEY_FORKS}{BS[1]} -C {PH_RANGE_MULTIPLIER}"
        )
        bash_cmd_copy_mets_chunk = f"cp -p ${BS[0]}{PARAMS_KEY_METS_PATH}{BS[1]} \\$mets_file_chunk"

        script = f'{SPACES}{SPACES}"""\n{SPACES}{SPACES}'
        script += f"current_range_pages=\\$("
        if environment == "apptainer" or environment == "docker":
            script += f"${BS[0]}{PARAMS_KEY_ENV_WRAPPER_CMD_CORE}{BS[1]} "
        script += f"{bash_cmd_ocrd_ws})\n"
        script += f'{SPACES}{SPACES}echo "Current range is: \\$current_range_pages"\n'

        if with_mets_server:
            script += f"{SPACES}{SPACES}mets_file_chunk=\\$(echo ${BS[0]}{PARAMS_KEY_METS_PATH}{BS[1]})\n"

        if not with_mets_server:
            script += f"{SPACES}{SPACES}mets_file_chunk=\\$(echo ${BS[0]}{PARAMS_KEY_WORKSPACE_DIR}{BS[1]}/mets_{PH_RANGE_MULTIPLIER}.xml)\n"
            script += f'{SPACES}{SPACES}echo "Mets file chunk path: \\$mets_file_chunk"\n'
            script += f"{SPACES}{SPACES}\\$("
            if environment == "apptainer" or environment == "docker":
                script += f"${BS[0]}{PARAMS_KEY_ENV_WRAPPER_CMD_CORE}{BS[1]} "
            script += f"{bash_cmd_copy_mets_chunk})\n"
        script += f'{SPACES}{SPACES}"""\n'
        block.script = script
        self.nf_process_split_range = block
        return block

    # TODO: Refactor later
    def build_merge_mets_process(self, environment: str) -> NextflowBlockProcess:
        block = NextflowBlockProcess(ProcessorCallArguments(executable="merging-mets"), 0)
        block.nf_process_name = "merging_mets"
        block.ocrd_command_bash = ""
        block.ocrd_command_bash_placeholders = ""

        block.add_directive(directive='debug', value='true')
        # Warning, do not set that to another value. Merging of mets must always be a single instance
        block.add_directive(directive='maxForks', value='1')
        if environment == "apptainer":
            block.add_directive(directive='cpus', value=PARAMS_KEY_CPUS_PER_FORK)
            block.add_directive(directive='memory', value=PARAMS_KEY_RAM_PER_FORK)

        block.add_parameter_input(parameter="mets_file_chunk", parameter_type="val")
        block.add_parameter_input(parameter="page_range", parameter_type="val")

        PH_METS_FILE_CHUNK = "${mets_file_chunk}"
        PH_PAGE_RANGE = "${page_range}"
        bash_cmd_ocrd_ws = (
            f"ocrd workspace -d ${BS[0]}{PARAMS_KEY_WORKSPACE_DIR}{BS[1]} "
            f"merge --force --no-copy-files {PH_METS_FILE_CHUNK} "
            f"--page-id {PH_PAGE_RANGE}"
        )
        script = f'{SPACES}{SPACES}"""\n{SPACES}{SPACES}'
        if environment == "apptainer" or environment == "docker":
            script += f"${BS[0]}{PARAMS_KEY_ENV_WRAPPER_CMD_CORE}{BS[1]} "
        script += f"{bash_cmd_ocrd_ws}\n{SPACES}{SPACES}"
        if environment == "apptainer" or environment == "docker":
            script += f"${BS[0]}{PARAMS_KEY_ENV_WRAPPER_CMD_CORE}{BS[1]} "
        script += f"rm {PH_METS_FILE_CHUNK}\n"
        script += f'{SPACES}{SPACES}"""\n'
        block.script = script
        self.nf_process_merging_mets = block
        return block

    def build_nextflow_processes(
        self, ocrd_processors: List[ProcessorCallArguments], environment: str, with_mets_server: bool = False
    ):
        index = 0
        env_wrapper = True if environment == "docker" or environment == "apptainer" else False
        self.build_split_page_ranges_process(environment=environment, with_mets_server=with_mets_server)
        self.build_merge_mets_process(environment=environment)
        for processor in ocrd_processors:
            nf_process_block = NextflowBlockProcess(processor, index, env_wrapper=env_wrapper)

            # Add Nextflow process directives
            nf_process_block.add_directive(directive='debug', value='true')
            nf_process_block.add_directive(directive='maxForks', value=PARAMS_KEY_FORKS)
            if environment == "apptainer":
                nf_process_block.add_directive(directive='cpus', value=PARAMS_KEY_CPUS_PER_FORK)
                nf_process_block.add_directive(directive='memory', value=PARAMS_KEY_RAM_PER_FORK)

            # Add Nextflow process parameters
            nf_process_block.add_parameter_input(parameter=CONST_METS_PATH, parameter_type='val')
            nf_process_block.add_parameter_input(parameter=CONST_PAGE_RANGE, parameter_type='val')
            nf_process_block.add_parameter_input(parameter=CONST_WORKSPACE_DIR, parameter_type='val')
            nf_process_block.add_parameter_input(parameter=CONST_DIR_IN, parameter_type='val')
            nf_process_block.add_parameter_input(parameter=CONST_DIR_OUT, parameter_type='val')

            nf_process_block.add_parameter_output(parameter=CONST_METS_PATH, parameter_type='val')
            nf_process_block.add_parameter_output(parameter=CONST_PAGE_RANGE, parameter_type='val')
            nf_process_block.add_parameter_output(parameter=CONST_WORKSPACE_DIR, parameter_type='val')
            self.nf_lines_parameters.append(f'{PARAMS_KEY_ENV_WRAPPER_CMD_STEP}{index} = "null"')
            self.nf_blocks_process.append(nf_process_block)
            index += 1

    def __assign_first_file_grps_param(self):
        first_file_grps = self.nf_blocks_process[0].processor_call_arguments.input_file_grps
        index = 0
        for parameter in self.nf_lines_parameters:
            if PARAMS_KEY_INPUT_FILE_GRP in parameter:
                self.nf_lines_parameters[index] = parameter.replace("null", first_file_grps)
                break
            index += 1

    def build_log_info_prints(self) -> str:
        log_info = f'log.info """\\\n'
        log_info += f"{SPACES}OPERANDI HPC - Nextflow Workflow\n"
        log_info += f"{SPACES}===================================================\n"
        for param in self.nf_lines_parameters:
            if not param or "params." not in param:
                continue
            param_key = param[param.find(".") + 1:param.find("=") - 1]
            log_info += f"{SPACES}{param_key}: "
            log_info += f'${BS[0]}{param[0:param.find("=") - 1]}{BS[1]}\n'
        log_info += f'{SPACES}""".stripIndent()\n'
        return log_info

    # TODO: Refactor later
    def build_main_workflow(self, with_mets_server: bool):
        self.__assign_first_file_grps_param()
        nf_workflow_block = NextflowBlockWorkflow(
            workflow_name="main",
            nf_processes=self.nf_blocks_process,
            nf_split_block=self.nf_process_split_range,
            nf_merge_mets=self.nf_process_merging_mets,
            with_mets_server=with_mets_server
        )
        self.nf_blocks_workflow.append(nf_workflow_block)

    # TODO: Refactor later
    def produce_nextflow_file(self, output_path: str, environment: str, with_mets_server: bool):
        # Write Nextflow line tokens to an output file
        with open(output_path, mode='w', encoding='utf-8') as nextflow_file:
            nextflow_file.write(f"{WORKFLOW_COMMENT}\n")
            for nextflow_line in self.nf_lines_parameters:
                nextflow_file.write(f'{nextflow_line}\n')
            nextflow_file.write("\n")
            nextflow_file.write(self.build_log_info_prints())
            nextflow_file.write("\n")
            nextflow_file.write(f'{self.nf_process_split_range.file_representation(local_script=True)}\n')
            for block in self.nf_blocks_process:
                nextflow_file.write(f'{block.file_representation(local_script=False)}\n')
            if not with_mets_server:
                nextflow_file.write(f'{self.nf_process_merging_mets.file_representation(local_script=True)}\n')
            for block in self.nf_blocks_workflow:
                nextflow_file.write(f'{block.file_representation()}\n')
