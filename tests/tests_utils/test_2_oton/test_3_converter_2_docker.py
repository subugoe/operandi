from tests.assets.oton.constants import EXPECTED_WF1, IN_TXT_WF1, OUT_NF_WF1_DOCKER
from tests.tests_utils.test_2_oton.assert_utils import (
    assert_common_features, assert_common_features_docker, assert_compare_workflow_blocks)


def test_convert_wf1_with_env_docker(oton_converter):
    nextflow_file_class = oton_converter.convert_oton_env_docker(IN_TXT_WF1, OUT_NF_WF1_DOCKER)
    assert_common_features(nextflow_file_class, 8, 1)
    assert_common_features_docker(nextflow_file_class)
    assert_compare_workflow_blocks(OUT_NF_WF1_DOCKER, EXPECTED_WF1)
