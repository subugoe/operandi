from tests.assets.oton.constants import (
    EXPECTED_WF1, EXPECTED_WF2, EXPECTED_WF3, EXPECTED_WF4,
    IN_TXT_WF1, IN_TXT_WF2, IN_TXT_WF3, IN_TXT_WF4,
    OUT_NF_WF1_LOCAL, OUT_NF_WF2_LOCAL, OUT_NF_WF3_LOCAL, OUT_NF_WF4_LOCAL
)
from tests.tests_utils.test_2_oton.assert_utils import (
    assert_common_features, assert_common_features_local, assert_compare_workflow_blocks)


def test_convert_wf1_with_env_local(oton_converter):
    nextflow_file_class = oton_converter.convert_oton_env_local(IN_TXT_WF1, OUT_NF_WF1_LOCAL)
    assert 'params.input_file_group = "OCR-D-IMG"' in nextflow_file_class.nf_lines_parameters
    assert_common_features(nextflow_file_class, 8, 1)
    assert_compare_workflow_blocks(OUT_NF_WF1_LOCAL, EXPECTED_WF1)


def test_convert_wf2_with_env_local(oton_converter):
    nextflow_file_class = oton_converter.convert_oton_env_local(IN_TXT_WF2, OUT_NF_WF2_LOCAL)
    assert 'params.input_file_group = "OCR-D-IMG"' in nextflow_file_class.nf_lines_parameters
    assert_common_features(nextflow_file_class, 7, 1)
    assert_common_features_local(nextflow_file_class)
    assert_compare_workflow_blocks(OUT_NF_WF2_LOCAL, EXPECTED_WF2)


def test_convert_wf3_with_env_local(oton_converter):
    nextflow_file_class = oton_converter.convert_oton_env_local(IN_TXT_WF3, OUT_NF_WF3_LOCAL)
    assert 'params.input_file_group = "OCR-D-GT-SEG-BLOCK,OCR-D-OCR"' in nextflow_file_class.nf_lines_parameters
    assert_common_features(nextflow_file_class, 3, 1)
    assert_common_features_local(nextflow_file_class)
    assert_compare_workflow_blocks(OUT_NF_WF3_LOCAL, EXPECTED_WF3)


def test_convert_wf4_with_env_local(oton_converter):
    nextflow_file_class = oton_converter.convert_oton_env_local(IN_TXT_WF4, OUT_NF_WF4_LOCAL)
    assert 'params.input_file_group = "OCR-D-IMG"' in nextflow_file_class.nf_lines_parameters
    assert_common_features(nextflow_file_class, 13, 1)
    assert_common_features_local(nextflow_file_class)
    assert_compare_workflow_blocks(OUT_NF_WF4_LOCAL, EXPECTED_WF4)
