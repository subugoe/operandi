from tests.assets.oton.constants import EXPECTED_WF1, IN_TXT_WF1, OUT_NF_WF1_APPTAINER
from tests.tests_utils.test_2_oton.assert_utils import (
    assert_common_features, assert_common_features_apptainer, assert_compare_workflow_blocks)


def test_convert_wf1_with_env_apptainer(oton_converter):
    nextflow_file_class = oton_converter.convert_oton_env_apptainer(IN_TXT_WF1, OUT_NF_WF1_APPTAINER)
    assert_common_features(nextflow_file_class, 8, 1)
    assert_common_features_apptainer(nextflow_file_class)
    assert_compare_workflow_blocks(OUT_NF_WF1_APPTAINER, EXPECTED_WF1)
