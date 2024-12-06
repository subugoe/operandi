from operandi_utils.oton.nf_block_process import NextflowBlockProcess
from operandi_utils.oton.ocrd_validator import OCRDValidator


def test_line_append():
    """Tests if each NextFlow function appends a number to the processor name
    distinguish processor calls
    """
    input_path = 'tests/assets/oton/workflow4.txt'
    validator = OCRDValidator()
    list_processor_call_arguments = validator.validate(input_path)

    result = []
    for ocrd_command in list_processor_call_arguments:
        index_pos = list_processor_call_arguments.index(ocrd_command)
        nextflow_process = NextflowBlockProcess(ocrd_command, index_pos, with_mets_server=False, env_wrapper=False)
        result.append(nextflow_process.nf_process_name)

    expected = [
        "ocrd_olena_binarize_0",
        "ocrd_anybaseocr_crop_1",
        "ocrd_olena_binarize_2",
        "ocrd_cis_ocropy_denoise_3",
        "ocrd_cis_ocropy_deskew_4",
        "ocrd_tesserocr_segment_region_5",
        "ocrd_segment_repair_6",
        "ocrd_cis_ocropy_deskew_7",
        "ocrd_cis_ocropy_clip_8",
        "ocrd_tesserocr_segment_line_9",
        "ocrd_segment_repair_10",
        "ocrd_cis_ocropy_dewarp_11",
        "ocrd_calamari_recognize_12"
    ]

    assert result == expected
