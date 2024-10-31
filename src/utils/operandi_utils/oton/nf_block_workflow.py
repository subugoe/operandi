from logging import getLevelName, getLogger
from typing import List
from operandi_utils.oton.constants import OTON_LOG_LEVEL, PARAMS_KEY_METS_PATH, PARAMS_KEY_INPUT_FILE_GRP, SPACES
from operandi_utils.oton.nf_block_process import NextflowBlockProcess


class NextflowBlockWorkflow:
    def __init__(self, workflow_name: str, nf_processes: List[NextflowBlockProcess]):
        self.logger = getLogger(__name__)
        self.logger.setLevel(getLevelName(OTON_LOG_LEVEL))

        self.workflow_name = workflow_name
        self.nf_blocks_process: List[NextflowBlockProcess] = nf_processes

    def file_representation(self):
        representation = 'workflow {\n'
        representation += f'{SPACES}{self.workflow_name}:\n'

        self.logger.info(self.nf_blocks_process)

        previous_nfp = None
        for nfp in self.nf_blocks_process:
            nfp_1 = nfp.processor_call_arguments.input_file_grps
            nfp_2 = nfp.processor_call_arguments.output_file_grps
            representation += f'{SPACES}{SPACES}{nfp.nf_process_name}('
            if previous_nfp is None:
                representation += f'{PARAMS_KEY_METS_PATH}, {PARAMS_KEY_INPUT_FILE_GRP}, "{nfp_2}")'
            else:
                representation += f'{previous_nfp}.out, "{nfp_1}", "{nfp_2}")'
            representation += f'\n'
            previous_nfp = nfp.nf_process_name

        representation += '}'

        self.logger.debug(f"\n{representation}")
        self.logger.info(f"Successfully created Nextflow Workflow: {self.workflow_name}")
        return representation
