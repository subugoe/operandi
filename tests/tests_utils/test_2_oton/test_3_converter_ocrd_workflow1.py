from operandi_utils.oton.oton_converter import OTONConverter
from re import sub
import os


def clean_up(path):
    """Cleans up test artifacts from file system
    """
    if os.path.isfile(path):
        os.remove(path)

INPUT_OCRD_PROCESS_WORKFLOW = 'tests/assets/workflows_oton/workflow1.txt'
OUTPUT_NEXTFLOW_WORKFLOW_LOCAL = 'tests/assets/workflows_oton/test_output_nextflow1.txt'
OUTPUT_NEXTFLOW_WORKFLOW_DOCKER = 'tests/assets/workflows_oton/test_output_nextflow1_docker1.txt'

# Test parameters based on INPUT_OCRD_PROCESS_WORKFLOW
TEST_PARAMETERS = [
    'params.input_file_group = "OCR-D-IMG"',
    'params.mets_path = "null"',
    'params.workspace_dir = "null"'
]

EXPECTED_MAIN_WORKFLOW = """
workflow {
    main:
        ocrd_cis_ocropy_binarize_0(params.mets_path, params.input_file_group, "OCR-D-BIN")
        ocrd_anybaseocr_crop_1(ocrd_cis_ocropy_binarize_0.out, "OCR-D-BIN", "OCR-D-CROP")
        ocrd_skimage_binarize_2(ocrd_anybaseocr_crop_1.out, "OCR-D-CROP", "OCR-D-BIN2")
        ocrd_skimage_denoise_3(ocrd_skimage_binarize_2.out, "OCR-D-BIN2", "OCR-D-BIN-DENOISE")
        ocrd_tesserocr_deskew_4(ocrd_skimage_denoise_3.out, "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
        ocrd_cis_ocropy_segment_5(ocrd_tesserocr_deskew_4.out, "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG")
        ocrd_cis_ocropy_dewarp_6(ocrd_cis_ocropy_segment_5.out, "OCR-D-SEG", "OCR-D-SEG-LINE-RESEG-DEWARP")
        ocrd_calamari_recognize_7(ocrd_cis_ocropy_dewarp_6.out, "OCR-D-SEG-LINE-RESEG-DEWARP", "OCR-D-OCR")
}
"""


def assert_common_features(nextflow_file_class, output_file_path):
    parameters = nextflow_file_class.nf_lines_parameters
    blocks_process = nextflow_file_class.nf_blocks_process
    blocks_workflows = nextflow_file_class.nf_blocks_workflow

    for parameter in TEST_PARAMETERS:
        assert parameter in parameters
    assert len(blocks_process) == 8
    assert len(blocks_workflows) == 1

    for block in blocks_process:
        assert block.directives == {"maxForks": "1"}
        assert len(block.input_params) == 3
        assert len(block.output_params) == 1
        dump_script = block.dump_script()
        assert "ocrd-" in dump_script

    for block in blocks_workflows:
        assert block.workflow_name == "main"

    expected_normalized = sub(r'\s+', '', EXPECTED_MAIN_WORKFLOW)
    with open(output_file_path, mode='r', encoding='utf-8') as fp:
        wf = fp.read()
        no_tab_string = sub(r'\t+', '', wf)
        no_spaces_result = sub(r'\s+', '', no_tab_string)
    # clean_up(output_file_path)
    assert expected_normalized in no_spaces_result


def test_conversion_with_env_local():
    oton_converter = OTONConverter()
    nextflow_file_class = oton_converter.convert_oton_env_local(
        input_path=INPUT_OCRD_PROCESS_WORKFLOW,
        output_path=OUTPUT_NEXTFLOW_WORKFLOW_LOCAL
    )
    assert_common_features(nextflow_file_class, OUTPUT_NEXTFLOW_WORKFLOW_LOCAL)


def test_conversion_with_env_docker():
    oton_converter = OTONConverter()
    nextflow_file_class = oton_converter.convert_oton_env_docker(
        input_path=INPUT_OCRD_PROCESS_WORKFLOW,
        output_path=OUTPUT_NEXTFLOW_WORKFLOW_DOCKER
    )
    assert 'params.env_wrapper = "null"' in nextflow_file_class.nf_lines_parameters
    assert_common_features(nextflow_file_class, OUTPUT_NEXTFLOW_WORKFLOW_DOCKER)
    for block in nextflow_file_class.nf_blocks_process:
        assert '${params.env_wrapper}' in block.file_representation()
