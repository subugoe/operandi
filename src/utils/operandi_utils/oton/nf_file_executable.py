from logging import getLevelName, getLogger
from typing import List, Tuple

from operandi_utils.oton.ocrd_validator import ProcessorCallArguments
from operandi_utils.oton.constants import (
    DIR_IN, DIR_OUT, METS_FILE,
    OTON_LOG_LEVEL,
    PARAMS_KEY_INPUT_FILE_GRP,
    REPR_ENV_WRAPPER,
    REPR_INPUT_FILE_GRP,
    REPR_METS_PATH,
    REPR_WORKSPACE_DIR,
    WORKFLOW_COMMENT
)
from operandi_utils.oton.nf_block_process import NextflowBlockProcess
from operandi_utils.oton.nf_block_workflow import NextflowBlockWorkflow


class NextflowFileExecutable:
    def __init__(self):
        self.logger = getLogger(__name__)
        self.logger.setLevel(getLevelName(OTON_LOG_LEVEL))

        self.nf_lines_parameters: List[str] = []
        self.nf_blocks_process: List[NextflowBlockProcess] = []
        self.nf_blocks_workflow: List[NextflowBlockWorkflow] = []

    def build_parameters_local(self):
        self.nf_lines_parameters.append('nextflow.enable.dsl = 2')
        self.nf_lines_parameters.append('')

        self.nf_lines_parameters.append(REPR_INPUT_FILE_GRP)
        self.nf_lines_parameters.append(REPR_METS_PATH)
        self.nf_lines_parameters.append(REPR_WORKSPACE_DIR)

        self.nf_lines_parameters.append('')

    def build_parameters_docker(self):
        self.nf_lines_parameters.append('nextflow.enable.dsl = 2')
        self.nf_lines_parameters.append('')

        self.nf_lines_parameters.append(REPR_INPUT_FILE_GRP)
        self.nf_lines_parameters.append(REPR_METS_PATH)
        self.nf_lines_parameters.append(REPR_WORKSPACE_DIR)

        self.nf_lines_parameters.append(REPR_ENV_WRAPPER)

        self.nf_lines_parameters.append('')

    def build_parameters_apptainer(self):
        raise NotImplemented("This feature is not implemented yet!")

    def build_nextflow_processes_local(self, ocrd_processor: List[ProcessorCallArguments]):
        index = 0
        for processor in ocrd_processor:
            nf_process_block = NextflowBlockProcess(processor, index, env_wrapper=False)
            nf_process_block.add_directive(directive='maxForks', value='1')
            nf_process_block.add_parameter_input(parameter=METS_FILE, parameter_type='path')
            nf_process_block.add_parameter_input(parameter=DIR_IN, parameter_type='val')
            nf_process_block.add_parameter_input(parameter=DIR_OUT, parameter_type='val')
            nf_process_block.add_parameter_output(parameter=METS_FILE, parameter_type='path')
            self.nf_blocks_process.append(nf_process_block)
            self.logger.info(f"Successfully created Nextflow Process: {nf_process_block.nf_process_name}")
            index += 1

    def build_nextflow_processes_docker(self, ocrd_processor: List[ProcessorCallArguments]):
        index = 0
        for processor in ocrd_processor:
            nf_process_block = NextflowBlockProcess(processor, index, env_wrapper=True)
            nf_process_block.add_directive(directive='maxForks', value='1')
            nf_process_block.add_parameter_input(parameter=METS_FILE, parameter_type='path')
            nf_process_block.add_parameter_input(parameter=DIR_IN, parameter_type='val')
            nf_process_block.add_parameter_input(parameter=DIR_OUT, parameter_type='val')
            nf_process_block.add_parameter_output(parameter=METS_FILE, parameter_type='path')
            self.nf_blocks_process.append(nf_process_block)
            self.logger.info(f"Successfully created Nextflow Process: {nf_process_block.nf_process_name}")
            index += 1

    def build_nextflow_processes_apptainer(self, ocrd_processor: List[ProcessorCallArguments]) -> Tuple[List[str], str]:
        raise NotImplemented("This feature is not implemented yet!")

    def __assign_first_file_grps_param(self):
        first_file_grps = self.nf_blocks_process[0].processor_call_arguments.input_file_grps
        index = 0
        for parameter in self.nf_lines_parameters:
            if PARAMS_KEY_INPUT_FILE_GRP in parameter:
                self.nf_lines_parameters[index] = parameter.replace("null", first_file_grps)
                break
            index += 1

    def build_main_workflow(self):
        self.__assign_first_file_grps_param()
        nf_workflow_block = NextflowBlockWorkflow(workflow_name="main", nf_processes=self.nf_blocks_process)
        self.nf_blocks_workflow.append(nf_workflow_block)

    def produce_nextflow_file(self, output_path: str):
        # Write Nextflow line tokens to an output file
        with open(output_path, mode='w', encoding='utf-8') as nextflow_file:
            nextflow_file.write(f"{WORKFLOW_COMMENT}\n")
            for nextflow_line in self.nf_lines_parameters:
                nextflow_file.write(f'{nextflow_line}\n')
            for block in self.nf_blocks_process:
                nextflow_file.write(f'{block.file_representation()}\n')
            for block in self.nf_blocks_workflow:
                nextflow_file.write(f'{block.file_representation()}\n')
