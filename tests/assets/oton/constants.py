OTON_RESOURCES_DIR = 'tests/assets/oton'

IN_TXT_WF1 = f'{OTON_RESOURCES_DIR}/workflow1.txt'
IN_TXT_WF2 = f'{OTON_RESOURCES_DIR}/workflow2.txt'
IN_TXT_WF3 = f'{OTON_RESOURCES_DIR}/workflow3.txt'
IN_TXT_WF4 = f'{OTON_RESOURCES_DIR}/workflow4.txt'

OUT_NF_WF1_APPTAINER = f'{OTON_RESOURCES_DIR}/test_output_nextflow1_apptainer.nf'
OUT_NF_WF1_DOCKER = f'{OTON_RESOURCES_DIR}/test_output_nextflow1_docker.nf'
OUT_NF_WF1_LOCAL = f'{OTON_RESOURCES_DIR}/test_output_nextflow1.nf'
OUT_NF_WF2_LOCAL = f'{OTON_RESOURCES_DIR}/test_output_nextflow2.nf'
OUT_NF_WF3_LOCAL = f'{OTON_RESOURCES_DIR}/test_output_nextflow3.nf'
OUT_NF_WF4_LOCAL = f'{OTON_RESOURCES_DIR}/test_output_nextflow4.nf'

INVALID_WF1 = f'{OTON_RESOURCES_DIR}/invalid_workflow1.txt'
INVALID_WF2 = f'{OTON_RESOURCES_DIR}/invalid_workflow2.txt'
INVALID_WF3 = f'{OTON_RESOURCES_DIR}/invalid_workflow3.txt'


EXPECTED_WF1 = """
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

EXPECTED_WF2 = """
workflow {
    main:
        ocrd_cis_ocropy_binarize_0(params.mets_path, params.input_file_group, "OCR-D-BIN")
        ocrd_anybaseocr_crop_1(ocrd_cis_ocropy_binarize_0.out, "OCR-D-BIN", "OCR-D-CROP")
        ocrd_skimage_denoise_2(ocrd_anybaseocr_crop_1.out, "OCR-D-CROP", "OCR-D-BIN-DENOISE")
        ocrd_tesserocr_deskew_3(ocrd_skimage_denoise_2.out, "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
        ocrd_tesserocr_segment_4(ocrd_tesserocr_deskew_3.out, "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG")
        ocrd_cis_ocropy_dewarp_5(ocrd_tesserocr_segment_4.out, "OCR-D-SEG", "OCR-D-SEG-DEWARP")
        ocrd_tesserocr_recognize_6(ocrd_cis_ocropy_dewarp_5.out, "OCR-D-SEG-DEWARP", "OCR-D-OCR")
}
"""

EXPECTED_WF3 = """
workflow {
    main:
        ocrd_dinglehopper_0(params.mets_path, params.input_file_group, "OCR-D-EVAL-SEG-BLOCK")
        ocrd_dinglehopper_1(ocrd_dinglehopper_0.out, "OCR-D-GT-SEG-LINE,OCR-D-OCR", "OCR-D-EVAL-SEG-LINE")
        ocrd_dinglehopper_2(ocrd_dinglehopper_1.out, "OCR-D-GT-SEG-PAGE,OCR-D-OCR", "OCR-D-EVAL-SEG-PAGE")
}
"""

EXPECTED_WF4 = """
workflow {
    main:
        ocrd_olena_binarize_0(params.mets_path, params.input_file_group, "OCR-D-BIN")
        ocrd_anybaseocr_crop_1(ocrd_olena_binarize_0.out, "OCR-D-BIN", "OCR-D-CROP")
        ocrd_olena_binarize_2(ocrd_anybaseocr_crop_1.out, "OCR-D-CROP", "OCR-D-BIN2")
        ocrd_cis_ocropy_denoise_3(ocrd_olena_binarize_2.out, "OCR-D-BIN2", "OCR-D-BIN-DENOISE")
        ocrd_cis_ocropy_deskew_4(ocrd_cis_ocropy_denoise_3.out, "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
        ocrd_tesserocr_segment_region_5(ocrd_cis_ocropy_deskew_4.out, "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG-REG")
        ocrd_segment_repair_6(ocrd_tesserocr_segment_region_5.out, "OCR-D-SEG-REG", "OCR-D-SEG-REPAIR")
        ocrd_cis_ocropy_deskew_7(ocrd_segment_repair_6.out, "OCR-D-SEG-REPAIR", "OCR-D-SEG-REG-DESKEW")
        ocrd_cis_ocropy_clip_8(ocrd_cis_ocropy_deskew_7.out, "OCR-D-SEG-REG-DESKEW", "OCR-D-SEG-REG-DESKEW-CLIP")
        ocrd_tesserocr_segment_line_9(ocrd_cis_ocropy_clip_8.out, "OCR-D-SEG-REG-DESKEW-CLIP", "OCR-D-SEG-LINE")
        ocrd_segment_repair_10(ocrd_tesserocr_segment_line_9.out, "OCR-D-SEG-LINE", "OCR-D-SEG-REPAIR-LINE")
        ocrd_cis_ocropy_dewarp_11(ocrd_segment_repair_10.out, "OCR-D-SEG-REPAIR-LINE", "OCR-D-SEG-LINE-RESEG-DEWARP")
        ocrd_calamari_recognize_12(ocrd_cis_ocropy_dewarp_11.out, "OCR-D-SEG-LINE-RESEG-DEWARP", "OCR-D-OCR")
}
"""

PARAMETERS_COMMON = [
    'nextflow.enable.dsl = 2',
    'params.mets_path = "null"',
    'params.workspace_dir = "null"'
]

PARAMETERS_LOCAL = []

PARAMETERS_DOCKER = [
    'params.env_wrapper = "null"'
]

PARAMETERS_APPTAINER = [
    'params.env_wrapper = "null"'
]
