import logging
from typing import List, Tuple

from operandi_utils.oton.validator import ProcessorCallArguments
from operandi_utils.oton.constants import (
    DIR_IN, DIR_OUT, METS_FILE,
    OTON_LOG_LEVEL,
    REPR_ENV_WRAPPER,
    REPR_INPUT_FILE_GRP,
    REPR_METS_PATH,
    REPR_WORKSPACE_DIR
)
from operandi_utils.oton.nf_block_process import NextflowBlockProcess
from operandi_utils.oton.nf_block_workflow import NextflowBlockWorkflow


class NextflowFileExecutable:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.getLevelName(OTON_LOG_LEVEL))

        self.nf_lines_parameters = []
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

    def build_nextflow_processes_local(self, ocrd_processor: List[ProcessorCallArguments]) -> Tuple[List[str], str]:
        nf_processes = []
        first_file_grps = "DEFAULT"
        index = 0
        for processor in ocrd_processor:
            nf_process_block = NextflowBlockProcess(processor, index, False)
            nf_process_block.add_directive(directive='maxForks', value='1')
            nf_process_block.add_parameter_input(parameter=METS_FILE, parameter_type='path')
            nf_process_block.add_parameter_input(parameter=DIR_IN, parameter_type='val')
            nf_process_block.add_parameter_input(parameter=DIR_OUT, parameter_type='val')
            nf_process_block.add_parameter_output(parameter=METS_FILE, parameter_type='path')
            self.nf_blocks_process.append(nf_process_block)

            # Take the input_file_grp of the first processor and change the value of the
            # REPR_INPUT_FILE_GRP to set the desired file group as default
            if index == 0:
                first_file_grps = nf_process_block.repr_in_workflow[1].strip('"')

            # This list is used when building the workflow
            nf_processes.append(nf_process_block.repr_in_workflow)
            self.logger.info(f"Successfully created Nextflow Process: {nf_process_block.nf_process_name}")
            index += 1
        return nf_processes, first_file_grps

    def build_nextflow_processes_docker(self, ocrd_processor: List[ProcessorCallArguments]) -> Tuple[List[str], str]:
        nf_processes = []
        first_file_grps = "DEFAULT"
        index = 0
        for processor in ocrd_processor:
            nf_process_block = NextflowBlockProcess(processor, index, True)
            nf_process_block.add_directive(directive='maxForks', value='1')
            nf_process_block.add_parameter_input(parameter=METS_FILE, parameter_type='path')
            nf_process_block.add_parameter_input(parameter=DIR_IN, parameter_type='val')
            nf_process_block.add_parameter_input(parameter=DIR_OUT, parameter_type='val')
            nf_process_block.add_parameter_output(parameter=METS_FILE, parameter_type='path')
            self.nf_blocks_process.append(nf_process_block)

            # Take the input_file_grp of the first processor and change the value of the
            # REPR_INPUT_FILE_GRP to set the desired file group as default
            if index == 0:
                first_file_grps = nf_process_block.repr_in_workflow[1].strip('"')

            # This list is used when building the workflow
            nf_processes.append(nf_process_block.repr_in_workflow)
            self.logger.info(f"Successfully created Nextflow Process: {nf_process_block.nf_process_name}")
            index += 1

        return nf_processes, first_file_grps

    def build_nextflow_processes_apptainer(self, ocrd_processor: List[ProcessorCallArguments]) -> Tuple[List[str], str]:
        raise NotImplemented("This feature is not implemented yet!")

    def build_main_workflow(self, nf_processes: List[str]):
        nf_workflow_block = NextflowBlockWorkflow("main", nf_processes)
        self.nf_blocks_workflow.append(nf_workflow_block)

    def produce_nextflow_file(self, output_path: str):
        # Write Nextflow line tokens to an output file
        with open(output_path, mode='w', encoding='utf-8') as nextflow_file:
            for nextflow_line in self.nf_lines_parameters:
                nextflow_file.write(f'{nextflow_line}\n')
            for block in self.nf_blocks_process:
                nextflow_file.write(f'{block.file_representation()}\n')
            for block in self.nf_blocks_workflow:
                nextflow_file.write(f'{block.file_representation()}\n')
