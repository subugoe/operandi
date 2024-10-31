# Added from https://github.com/MehmedGIT/OtoN_Converter/tree/master
import logging
from typing import List
from ..constants import (
    OTON_LOG_LEVEL,
    OTON_LOG_FORMAT,
)
from .constants import (
    PARAMS_KEY_METS_PATH,
    PARAMS_KEY_INPUT_FILE_GRP,
    SPACES
)


class NextflowBlockWorkflow:
    def __init__(self, workflow_name: str, nf_processes: List[str]):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.getLevelName(OTON_LOG_LEVEL))
        logging.basicConfig(format=OTON_LOG_FORMAT)

        self.workflow_name = workflow_name
        self.nf_processes: List[str] = nf_processes

    def file_representation(self):
        representation = 'workflow {\n'
        representation += f'{SPACES}{self.workflow_name}:\n'

        previous_nfp = None
        for nfp in self.nf_processes:
            nfp_0 = nfp[0]
            nfp_1 = nfp[1]
            nfp_2 = nfp[2]
            if previous_nfp is None:
                representation += f'{SPACES}{SPACES}{nfp_0}({PARAMS_KEY_METS_PATH}, {PARAMS_KEY_INPUT_FILE_GRP}, {nfp_2})\n'
            else:
                representation += f'{SPACES}{SPACES}{nfp_0}({previous_nfp}.out, {nfp_1}, {nfp_2})\n'
            previous_nfp = nfp_0

        representation += '}'

        self.logger.debug(f"\n{representation}")
        self.logger.info(f"Successfully created Nextflow Workflow: {self.workflow_name}")
        return representation
