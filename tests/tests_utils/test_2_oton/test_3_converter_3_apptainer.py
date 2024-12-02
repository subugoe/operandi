from tests.assets.oton.constants import (
    EXPECTED_WF1, EXPECTED_WF1_WITH_MS, IN_TXT_WF1, OUT_NF_WF1_APPTAINER, OUT_NF_WF1_APPTAINER_WITH_MS)
from tests.tests_utils.test_2_oton.assert_utils import (
    assert_common_features, assert_common_features_apptainer, assert_compare_workflow_blocks)


def test_convert_wf1_with_env_apptainer(oton_converter):
    nextflow_file_class = oton_converter.convert_oton(IN_TXT_WF1, OUT_NF_WF1_APPTAINER, "apptainer", False)
    assert_common_features(nextflow_file_class, 8, 1, False)
    assert_common_features_apptainer(nextflow_file_class)
    assert_compare_workflow_blocks(OUT_NF_WF1_APPTAINER, EXPECTED_WF1)

def test_convert_wf1_with_env_apptainer_with_mets_server(oton_converter):
    nextflow_file_class = oton_converter.convert_oton(IN_TXT_WF1, OUT_NF_WF1_APPTAINER_WITH_MS, "apptainer", True)
    assert_common_features(nextflow_file_class, 8, 1, True)
    assert_common_features_apptainer(nextflow_file_class)
    assert_compare_workflow_blocks(OUT_NF_WF1_APPTAINER_WITH_MS, EXPECTED_WF1_WITH_MS)
