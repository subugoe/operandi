from typing import List, Tuple
from operandi_utils.constants import StateJobSlurm


def parse_slurm_job_state_from_output(output: List[str]) -> Tuple[StateJobSlurm, str]:
    if not output:
        return StateJobSlurm.UNSET, "No output available, something is odd."
    if len(output) < 3:
        return StateJobSlurm.UNSET, f"Less than 3 lines in the output: {output}"
    try:
        parsed_state: str = output[-2].split()[1]
        if parsed_state.startswith("-"):
            parsed_state: str = output[-1].split()[1]
    except IndexError:
        return StateJobSlurm.UNSET, f"Parsing error from output: {output}"
    try:
        state_job_slurm = StateJobSlurm(parsed_state)
    except ValueError:
        return StateJobSlurm.UNSET, f"Unknown parsed state: {parsed_state} from output: {output}"
    return state_job_slurm, "Parsed state recognized"
