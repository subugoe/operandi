from os import remove
from os.path import isfile
from re import sub


from tests.assets.oton.constants import PARAMETERS_APPTAINER, PARAMETERS_COMMON, PARAMETERS_DOCKER, PARAMETERS_LOCAL


def assert_common_features(
    nextflow_file_class, num_blocks_process: int, num_blocks_workflow: int, with_mets_server: bool
):
    parameters = nextflow_file_class.nf_lines_parameters
    for parameter in PARAMETERS_COMMON:
        assert parameter in parameters
    if with_mets_server:
        assert parameters['params.mets_socket_path'] == '"null"', f"params.mets_socket_path is missing in {parameters}"
    blocks_process = nextflow_file_class.nf_blocks_process
    assert len(blocks_process) == num_blocks_process
    for block in blocks_process:
        assert "ocrd-" in block.ocrd_command_bash_placeholders
        if with_mets_server:
            assert "-U" in block.ocrd_command_bash_placeholders
    blocks_workflows = nextflow_file_class.nf_blocks_workflow
    assert len(blocks_workflows) == num_blocks_workflow
    for block in blocks_workflows:
        assert block.workflow_name == "main"


def assert_common_features_local(nextflow_file_class):
    parameters = nextflow_file_class.nf_lines_parameters
    for parameter in PARAMETERS_LOCAL:
        assert parameter in parameters, f"{parameter} is not in {parameters}"
    blocks_process = nextflow_file_class.nf_blocks_process
    for block in blocks_process:
        assert 'params.env_wrapper_cmd_step' not in block.dump_script(), \
            "params.env_wrapper_cmd_step found but should not exist in " + f"'{block.ocrd_command_bash_placeholders}'"


def assert_common_features_docker(nextflow_file_class):
    parameters = nextflow_file_class.nf_lines_parameters
    for parameter in PARAMETERS_DOCKER:
        assert parameter in parameters, f"{parameter} is not in {parameters}"
    blocks_process = nextflow_file_class.nf_blocks_process
    for block in blocks_process:
        assert 'params.env_wrapper_cmd_step' in block.dump_script(), \
            "params.env_wrapper_cmd_step not found but should exist in " + f"'{block.ocrd_command_bash_placeholders}'"


def assert_common_features_apptainer(nextflow_file_class):
    parameters = nextflow_file_class.nf_lines_parameters
    for parameter in PARAMETERS_APPTAINER:
        assert parameter in parameters, f"{parameter} is not in {parameters}"
    blocks_process = nextflow_file_class.nf_blocks_process
    for block in blocks_process:
        assert 'params.env_wrapper_cmd_step' in block.dump_script(), \
            "params.env_wrapper_cmd_step not found but should exist in " + f"'{block.ocrd_command_bash_placeholders}'"


def assert_compare_workflow_blocks(output_file_path, expected_wf, clean_files: bool = False):
    expected_normalized = sub(r'\s+', '', expected_wf)
    with open(output_file_path, mode='r', encoding='utf-8') as fp:
        wf = fp.read()
        no_tab_string = sub(r'\t+', '', wf)
        no_spaces_result = sub(r'\s+', '', no_tab_string)
    if clean_files and isfile(output_file_path):
        remove(output_file_path)
    assert expected_normalized in no_spaces_result
