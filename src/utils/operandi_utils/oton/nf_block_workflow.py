from logging import getLevelName, getLogger
from typing import List
from operandi_utils.oton.constants import OTON_LOG_LEVEL, PARAMS_KEY_INPUT_FILE_GRP, PARAMS_KEY_FORKS, SPACES
from operandi_utils.oton.nf_block_process import NextflowBlockProcess

class NextflowBlockWorkflow:
    def __init__(
        self, workflow_name: str,
        nf_processes: List[NextflowBlockProcess],
        nf_split_block: NextflowBlockProcess,
        nf_merge_mets: NextflowBlockProcess,
        with_mets_server: bool = False
    ):
        self.logger = getLogger(__name__)
        self.logger.setLevel(getLevelName(OTON_LOG_LEVEL))

        self.with_mets_server = with_mets_server
        self.workflow_name = workflow_name
        self.workflow_calls: List[str] = []
        self.produce_workflow_calls(nf_processes, nf_split_block, nf_merge_mets)

    def produce_workflow_calls(
        self,
        nf_blocks_process: List[NextflowBlockProcess],
        nf_split_page_ranges: NextflowBlockProcess,
        nf_merge_mets: NextflowBlockProcess
    ):
        self.workflow_calls.append(f"ch_range_multipliers = Channel.of(0..{PARAMS_KEY_FORKS}.intValue()-1)\n")
        self.workflow_calls.append(f"{nf_split_page_ranges.nf_process_name}(ch_range_multipliers)\n")
        previous_nfp = None
        for block_process in nf_blocks_process:
            in_file_grps = block_process.processor_call_arguments.input_file_grps
            out_file_grps = block_process.processor_call_arguments.output_file_grps
            workflow_call = f"{block_process.nf_process_name}("
            if previous_nfp is None:
                workflow_call += (
                    f'{nf_split_page_ranges.nf_process_name}.out[0], {nf_split_page_ranges.nf_process_name}.out[1], '
                    f'{PARAMS_KEY_INPUT_FILE_GRP}, "{out_file_grps}"'
                )
            else:
                workflow_call += (
                    f'{previous_nfp}.out[0], {previous_nfp}.out[1], "{in_file_grps}",'
                    f' "{out_file_grps}"'
                )
            workflow_call += ")\n"
            previous_nfp = block_process.nf_process_name
            self.workflow_calls.append(workflow_call)
        if not self.with_mets_server:
            self.workflow_calls.append(
                f"{nf_merge_mets.nf_process_name}({previous_nfp}.out[0], {previous_nfp}.out[1])\n")

    def file_representation(self):
        representation = 'workflow {\n'
        representation += f'{SPACES}{self.workflow_name}:\n'
        for workflow_call in self.workflow_calls:
            representation += f"{SPACES}{SPACES}{workflow_call}"
        representation += '}'
        return representation
