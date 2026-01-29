from operandi_utils.constants import StateJobSlurm
from operandi_utils.hpc.nhr_executor_utils import parse_slurm_job_state_from_output


def test_parse_slurm_job_state_from_output_none_and_empty():
    test_output = None
    slurm_job_state, msg = parse_slurm_job_state_from_output(test_output)
    assert msg == "No output available, something is odd."
    assert slurm_job_state == StateJobSlurm.UNSET

    test_output = []
    slurm_job_state, msg = parse_slurm_job_state_from_output(test_output)
    assert msg == "No output available, something is odd."
    assert slurm_job_state == StateJobSlurm.UNSET


def test_parse_slurm_job_state_from_output_less_lines():
    test_output_out_of_memory = [
        "'JobID                State                ExitCode \n',",
        "'-------------------- -------------------- -------- \n'"
    ]
    slurm_job_state, msg = parse_slurm_job_state_from_output(test_output_out_of_memory)
    assert msg == f"Less than 3 lines in the output: {test_output_out_of_memory}"
    assert slurm_job_state == StateJobSlurm.UNSET


def test_parse_slurm_job_state_from_output_valid_states():
    # Example output for reference:
    # sacct -j 6313216 --format=jobid%-20,state%-20,exitcode
    test_output_out_of_memory = [
        "'JobID                State                ExitCode \n'",
        "'-------------------- -------------------- -------- \n'",
        "'6313216               OUT_OF_MEMORY           0:125 \n'",
        "'6313216.batch         OUT_OF_MEMORY           0:125 \n'",
        "'6313216.extern        COMPLETED                 0:0 \n'"
    ]
    slurm_job_state, msg = parse_slurm_job_state_from_output(test_output_out_of_memory)
    assert msg == "Parsed state recognized"
    assert slurm_job_state == StateJobSlurm.OUT_OF_MEMORY

    test_output_completed = [
        "'JobID                State                ExitCode \n'",
        "'-------------------- -------------------- -------- \n'",
        "'6313216              COMPLETED                 0:0 \n'",
        "'6313216.batch        COMPLETED                 0:0 \n'",
        "'6313216.extern       COMPLETED                 0:0 \n'"
    ]
    slurm_job_state, msg = parse_slurm_job_state_from_output(test_output_completed)
    assert msg == "Parsed state recognized"
    assert slurm_job_state == StateJobSlurm.COMPLETED

    test_output_failed = [
        "'JobID                State                ExitCode \n'",
        "'-------------------- -------------------- -------- \n'",
        "'6313216              FAILED                    0:0 \n'",
        "'6313216.batch        FAILED                    0:0 \n'",
        "'6313216.extern       COMPLETED                 0:0 \n'"
    ]
    slurm_job_state, msg = parse_slurm_job_state_from_output(test_output_failed)
    assert msg == "Parsed state recognized"
    assert slurm_job_state == StateJobSlurm.FAILED


def test_parse_slurm_job_state_from_output_invalid_state():
    test_output_out_of_memory = [
        "'JobID                State                ExitCode \n'",
        "'-------------------- -------------------- -------- \n'",
        "'6313216               OUT_OF_ME+           0:125 \n'",
        "'6313216.batch         OUT_OF_ME+           0:125 \n'",
        "'6313216.extern        COMPLETED                 0:0 \n'"
    ]
    slurm_job_state, msg = parse_slurm_job_state_from_output(test_output_out_of_memory)
    assert msg == f"Unknown parsed state: OUT_OF_ME+ from output: {test_output_out_of_memory}"
    assert slurm_job_state == StateJobSlurm.UNSET
