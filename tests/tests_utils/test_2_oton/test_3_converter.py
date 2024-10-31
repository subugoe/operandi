from operandi_utils.oton.oton_converter import OTONConverter
from re import sub
import os


def clean_up(path):
    """Cleans up test artifacts from file system
    """
    if os.path.isfile(path):
        os.remove(path)


def test_conversion_with_env_local():
    """E2E test for an OCR-D workflow conversion using native ocrd_all
    """
    oton_converter = OTONConverter()
    input_path = 'tests/assets/workflows_oton/workflow1.txt'
    output_path = 'tests/assets/workflows_oton/test_output_nextflow1.txt'
    nextflow_file_class = oton_converter.convert_oton_env_local(input_path=input_path, output_path=output_path)
    assert 'params.input_file_group = "OCR-D-IMG"' in nextflow_file_class.nf_lines_parameters
    assert 'params.mets_path = "null"' in nextflow_file_class.nf_lines_parameters
    assert 'params.workspace_dir = "null"' in nextflow_file_class.nf_lines_parameters

    expected_workflow = """workflow {
            main:
                ocrd_cis_ocropy_binarize_0(params.mets_path, params.input_file_group, "OCR-D-BIN")
                ocrd_anybaseocr_crop_1(ocrd_cis_ocropy_binarize_0.out, "OCR-D-BIN", "OCR-D-CROP")
                ocrd_skimage_binarize_2(ocrd_anybaseocr_crop_1.out, "OCR-D-CROP", "OCR-D-BIN2")
                ocrd_skimage_denoise_3(ocrd_skimage_binarize_2.out, "OCR-D-BIN2", "OCR-D-BIN-DENOISE")
                ocrd_tesserocr_deskew_4(ocrd_skimage_denoise_3.out, "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
                ocrd_cis_ocropy_segment_5(ocrd_tesserocr_deskew_4.out, "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG")
                ocrd_cis_ocropy_dewarp_6(ocrd_cis_ocropy_segment_5.out, "OCR-D-SEG", "OCR-D-SEG-LINE-RESEG-DEWARP")
                ocrd_calamari_recognize_7(ocrd_cis_ocropy_dewarp_6.out, "OCR-D-SEG-LINE-RESEG-DEWARP", "OCR-D-OCR")
        }"""
    expected_normalized = sub(r'\s+', '', expected_workflow)

    with open(output_path, mode='r', encoding='utf-8') as fp:
        wf = fp.read()
        no_tab_string = sub(r'\t+', '', wf)
        no_spaces_result = sub(r'\s+', '', no_tab_string)

    # clean_up(output_path)

    assert expected_normalized in no_spaces_result


def test_conversion_with_env_docker():
    """E2E test for an OCR-D workflow conversion using the Docker flag.
    We test for success by looking for an exemplary line that is executed by Docker.
    """

    input_path = 'tests/assets/workflows_oton/workflow1.txt'
    output_path = 'tests/assets/workflows_oton/test_output_nextflow1_docker1.txt'

    oton_converter = OTONConverter()
    nextflow_file_class = oton_converter.convert_oton_env_docker(input_path=input_path, output_path=output_path)

    expected = '${params.env_wrapper} ocrd-cis-ocropy-binarize -m ${mets_file} -I ${input_file_group} -O ${output_file_group}'

    with open(output_path, mode='r', encoding='utf-8') as fp:
        wf = fp.read()
    # clean_up(output_path)
    assert expected in wf
