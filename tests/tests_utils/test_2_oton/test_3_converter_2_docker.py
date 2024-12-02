from tests.assets.oton.constants import (
    EXPECTED_WF1, EXPECTED_WF1_WITH_MS, IN_TXT_WF1, OUT_NF_WF1_DOCKER, OUT_NF_WF1_DOCKER_WITH_MS)
from tests.tests_utils.test_2_oton.assert_utils import (
    assert_common_features, assert_common_features_docker, assert_compare_workflow_blocks)


def test_convert_wf1_with_env_docker(oton_converter):
    nextflow_file_class = oton_converter.convert_oton(IN_TXT_WF1, OUT_NF_WF1_DOCKER, "docker", False)
    assert_common_features(nextflow_file_class, 8, 1, False)
    assert_common_features_docker(nextflow_file_class)
    assert_compare_workflow_blocks(OUT_NF_WF1_DOCKER, EXPECTED_WF1)

def test_convert_wf1_with_env_docker_with_mets_server(oton_converter):
    nextflow_file_class = oton_converter.convert_oton(IN_TXT_WF1, OUT_NF_WF1_DOCKER_WITH_MS, "docker", True)
    assert_common_features(nextflow_file_class, 8, 1, True)
    assert_common_features_docker(nextflow_file_class)
    assert_compare_workflow_blocks(OUT_NF_WF1_DOCKER_WITH_MS, EXPECTED_WF1_WITH_MS)
