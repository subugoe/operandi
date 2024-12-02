OTON_RESOURCES_DIR = 'tests/assets/oton'

IN_TXT_WF1 = f'{OTON_RESOURCES_DIR}/workflow1.txt'
IN_TXT_WF2 = f'{OTON_RESOURCES_DIR}/workflow2.txt'
IN_TXT_WF3 = f'{OTON_RESOURCES_DIR}/workflow3.txt'
IN_TXT_WF4 = f'{OTON_RESOURCES_DIR}/workflow4.txt'

OUT_NF_WF1_APPTAINER = f'{OTON_RESOURCES_DIR}/test_output_nextflow1_apptainer.nf'
OUT_NF_WF1_APPTAINER_WITH_MS = f'{OTON_RESOURCES_DIR}/test_output_nextflow1_apptainer_with_MS.nf'
OUT_NF_WF1_DOCKER = f'{OTON_RESOURCES_DIR}/test_output_nextflow1_docker.nf'
OUT_NF_WF1_DOCKER_WITH_MS = f'{OTON_RESOURCES_DIR}/test_output_nextflow1_docker_with_MS.nf'
OUT_NF_WF1_LOCAL = f'{OTON_RESOURCES_DIR}/test_output_nextflow1_local.nf'
OUT_NF_WF1_LOCAL_WITH_MS = f'{OTON_RESOURCES_DIR}/test_output_nextflow1_local_with_MS.nf'
OUT_NF_WF2_LOCAL = f'{OTON_RESOURCES_DIR}/test_output_nextflow2.nf'
OUT_NF_WF3_LOCAL = f'{OTON_RESOURCES_DIR}/test_output_nextflow3.nf'
OUT_NF_WF4_LOCAL = f'{OTON_RESOURCES_DIR}/test_output_nextflow4.nf'



INVALID_WF1 = f'{OTON_RESOURCES_DIR}/invalid_workflow1.txt'
INVALID_WF2 = f'{OTON_RESOURCES_DIR}/invalid_workflow2.txt'
INVALID_WF3 = f'{OTON_RESOURCES_DIR}/invalid_workflow3.txt'


EXPECTED_WF1 = """
workflow {
    main:
        ch_range_multipliers = Channel.of(0..params.forks.intValue()-1)
        split_page_ranges(ch_range_multipliers)
        ocrd_cis_ocropy_binarize_0(split_page_ranges.out[0], split_page_ranges.out[1], params.workspace_dir, params.input_file_group, "OCR-D-BIN")
        ocrd_anybaseocr_crop_1(ocrd_cis_ocropy_binarize_0.out[0], ocrd_cis_ocropy_binarize_0.out[1], ocrd_cis_ocropy_binarize_0.out[2], "OCR-D-BIN", "OCR-D-CROP")
        ocrd_skimage_binarize_2(ocrd_anybaseocr_crop_1.out[0], ocrd_anybaseocr_crop_1.out[1], ocrd_anybaseocr_crop_1.out[2], "OCR-D-CROP", "OCR-D-BIN2")
        ocrd_skimage_denoise_3(ocrd_skimage_binarize_2.out[0], ocrd_skimage_binarize_2.out[1], ocrd_skimage_binarize_2.out[2], "OCR-D-BIN2", "OCR-D-BIN-DENOISE")
        ocrd_tesserocr_deskew_4(ocrd_skimage_denoise_3.out[0], ocrd_skimage_denoise_3.out[1], ocrd_skimage_denoise_3.out[2], "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
        ocrd_cis_ocropy_segment_5(ocrd_tesserocr_deskew_4.out[0], ocrd_tesserocr_deskew_4.out[1], ocrd_tesserocr_deskew_4.out[2], "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG")
        ocrd_cis_ocropy_dewarp_6(ocrd_cis_ocropy_segment_5.out[0], ocrd_cis_ocropy_segment_5.out[1], ocrd_cis_ocropy_segment_5.out[2], "OCR-D-SEG", "OCR-D-SEG-LINE-RESEG-DEWARP")
        ocrd_calamari_recognize_7(ocrd_cis_ocropy_dewarp_6.out[0], ocrd_cis_ocropy_dewarp_6.out[1], ocrd_cis_ocropy_dewarp_6.out[2], "OCR-D-SEG-LINE-RESEG-DEWARP", "OCR-D-OCR")
        merging_mets(ocrd_calamari_recognize_7.out[0], ocrd_calamari_recognize_7.out[1])
}
"""

EXPECTED_WF1_WITH_MS = """
workflow {
    main:
        ch_range_multipliers = Channel.of(0..params.forks.intValue()-1)
        split_page_ranges(ch_range_multipliers)
        ocrd_cis_ocropy_binarize_0(split_page_ranges.out[0], split_page_ranges.out[1], params.workspace_dir, params.input_file_group, "OCR-D-BIN")
        ocrd_anybaseocr_crop_1(ocrd_cis_ocropy_binarize_0.out[0], ocrd_cis_ocropy_binarize_0.out[1], ocrd_cis_ocropy_binarize_0.out[2], "OCR-D-BIN", "OCR-D-CROP")
        ocrd_skimage_binarize_2(ocrd_anybaseocr_crop_1.out[0], ocrd_anybaseocr_crop_1.out[1], ocrd_anybaseocr_crop_1.out[2], "OCR-D-CROP", "OCR-D-BIN2")
        ocrd_skimage_denoise_3(ocrd_skimage_binarize_2.out[0], ocrd_skimage_binarize_2.out[1], ocrd_skimage_binarize_2.out[2], "OCR-D-BIN2", "OCR-D-BIN-DENOISE")
        ocrd_tesserocr_deskew_4(ocrd_skimage_denoise_3.out[0], ocrd_skimage_denoise_3.out[1], ocrd_skimage_denoise_3.out[2], "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
        ocrd_cis_ocropy_segment_5(ocrd_tesserocr_deskew_4.out[0], ocrd_tesserocr_deskew_4.out[1], ocrd_tesserocr_deskew_4.out[2], "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG")
        ocrd_cis_ocropy_dewarp_6(ocrd_cis_ocropy_segment_5.out[0], ocrd_cis_ocropy_segment_5.out[1], ocrd_cis_ocropy_segment_5.out[2], "OCR-D-SEG", "OCR-D-SEG-LINE-RESEG-DEWARP")
        ocrd_calamari_recognize_7(ocrd_cis_ocropy_dewarp_6.out[0], ocrd_cis_ocropy_dewarp_6.out[1], ocrd_cis_ocropy_dewarp_6.out[2], "OCR-D-SEG-LINE-RESEG-DEWARP", "OCR-D-OCR")
}
"""

EXPECTED_WF2 = """
workflow {
    main:
        ch_range_multipliers = Channel.of(0..params.forks.intValue()-1)
        split_page_ranges(ch_range_multipliers)
        ocrd_cis_ocropy_binarize_0(split_page_ranges.out[0], split_page_ranges.out[1], params.workspace_dir, params.input_file_group, "OCR-D-BIN")
        ocrd_anybaseocr_crop_1(ocrd_cis_ocropy_binarize_0.out[0], ocrd_cis_ocropy_binarize_0.out[1], ocrd_cis_ocropy_binarize_0.out[2], "OCR-D-BIN", "OCR-D-CROP")
        ocrd_skimage_denoise_2(ocrd_anybaseocr_crop_1.out[0], ocrd_anybaseocr_crop_1.out[1], ocrd_anybaseocr_crop_1.out[2], "OCR-D-CROP", "OCR-D-BIN-DENOISE")
        ocrd_tesserocr_deskew_3(ocrd_skimage_denoise_2.out[0], ocrd_skimage_denoise_2.out[1], ocrd_skimage_denoise_2.out[2], "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
        ocrd_tesserocr_segment_4(ocrd_tesserocr_deskew_3.out[0], ocrd_tesserocr_deskew_3.out[1], ocrd_tesserocr_deskew_3.out[2], "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG")
        ocrd_cis_ocropy_dewarp_5(ocrd_tesserocr_segment_4.out[0], ocrd_tesserocr_segment_4.out[1], ocrd_tesserocr_segment_4.out[2], "OCR-D-SEG", "OCR-D-SEG-DEWARP")
        ocrd_tesserocr_recognize_6(ocrd_cis_ocropy_dewarp_5.out[0], ocrd_cis_ocropy_dewarp_5.out[1], ocrd_cis_ocropy_dewarp_5.out[2], "OCR-D-SEG-DEWARP", "OCR-D-OCR")
        merging_mets(ocrd_tesserocr_recognize_6.out[0], ocrd_tesserocr_recognize_6.out[1])
}
"""

EXPECTED_WF3 = """
workflow {
    main:
        ch_range_multipliers = Channel.of(0..params.forks.intValue()-1)
        split_page_ranges(ch_range_multipliers)
        ocrd_dinglehopper_0(split_page_ranges.out[0], split_page_ranges.out[1], params.workspace_dir, params.input_file_group, "OCR-D-EVAL-SEG-BLOCK")
        ocrd_dinglehopper_1(ocrd_dinglehopper_0.out[0], ocrd_dinglehopper_0.out[1], ocrd_dinglehopper_0.out[2], "OCR-D-GT-SEG-LINE,OCR-D-OCR", "OCR-D-EVAL-SEG-LINE")
        ocrd_dinglehopper_2(ocrd_dinglehopper_1.out[0], ocrd_dinglehopper_1.out[1], ocrd_dinglehopper_1.out[2], "OCR-D-GT-SEG-PAGE,OCR-D-OCR", "OCR-D-EVAL-SEG-PAGE")
        merging_mets(ocrd_dinglehopper_2.out[0], ocrd_dinglehopper_2.out[1])
}
"""

EXPECTED_WF4 = """
workflow {
    main:
        ch_range_multipliers = Channel.of(0..params.forks.intValue()-1)
        split_page_ranges(ch_range_multipliers)
        ocrd_olena_binarize_0(split_page_ranges.out[0], split_page_ranges.out[1], params.workspace_dir, params.input_file_group, "OCR-D-BIN")
        ocrd_anybaseocr_crop_1(ocrd_olena_binarize_0.out[0], ocrd_olena_binarize_0.out[1], ocrd_olena_binarize_0.out[2], "OCR-D-BIN", "OCR-D-CROP")
        ocrd_olena_binarize_2(ocrd_anybaseocr_crop_1.out[0], ocrd_anybaseocr_crop_1.out[1], ocrd_anybaseocr_crop_1.out[2], "OCR-D-CROP", "OCR-D-BIN2")
        ocrd_cis_ocropy_denoise_3(ocrd_olena_binarize_2.out[0], ocrd_olena_binarize_2.out[1], ocrd_olena_binarize_2.out[2], "OCR-D-BIN2", "OCR-D-BIN-DENOISE")
        ocrd_cis_ocropy_deskew_4(ocrd_cis_ocropy_denoise_3.out[0], ocrd_cis_ocropy_denoise_3.out[1], ocrd_cis_ocropy_denoise_3.out[2], "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
        ocrd_tesserocr_segment_region_5(ocrd_cis_ocropy_deskew_4.out[0], ocrd_cis_ocropy_deskew_4.out[1], ocrd_cis_ocropy_deskew_4.out[2], "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG-REG")
        ocrd_segment_repair_6(ocrd_tesserocr_segment_region_5.out[0], ocrd_tesserocr_segment_region_5.out[1], ocrd_tesserocr_segment_region_5.out[2], "OCR-D-SEG-REG", "OCR-D-SEG-REPAIR")
        ocrd_cis_ocropy_deskew_7(ocrd_segment_repair_6.out[0], ocrd_segment_repair_6.out[1], ocrd_segment_repair_6.out[2], "OCR-D-SEG-REPAIR", "OCR-D-SEG-REG-DESKEW")
        ocrd_cis_ocropy_clip_8(ocrd_cis_ocropy_deskew_7.out[0], ocrd_cis_ocropy_deskew_7.out[1], ocrd_cis_ocropy_deskew_7.out[2], "OCR-D-SEG-REG-DESKEW", "OCR-D-SEG-REG-DESKEW-CLIP")
        ocrd_tesserocr_segment_line_9(ocrd_cis_ocropy_clip_8.out[0], ocrd_cis_ocropy_clip_8.out[1], ocrd_cis_ocropy_clip_8.out[2], "OCR-D-SEG-REG-DESKEW-CLIP", "OCR-D-SEG-LINE")
        ocrd_segment_repair_10(ocrd_tesserocr_segment_line_9.out[0], ocrd_tesserocr_segment_line_9.out[1], ocrd_tesserocr_segment_line_9.out[2], "OCR-D-SEG-LINE", "OCR-D-SEG-REPAIR-LINE")
        ocrd_cis_ocropy_dewarp_11(ocrd_segment_repair_10.out[0], ocrd_segment_repair_10.out[1], ocrd_segment_repair_10.out[2], "OCR-D-SEG-REPAIR-LINE", "OCR-D-SEG-LINE-RESEG-DEWARP")
        ocrd_calamari_recognize_12(ocrd_cis_ocropy_dewarp_11.out[0], ocrd_cis_ocropy_dewarp_11.out[1], ocrd_cis_ocropy_dewarp_11.out[2], "OCR-D-SEG-LINE-RESEG-DEWARP", "OCR-D-OCR")
        merging_mets(ocrd_calamari_recognize_12.out[0], ocrd_calamari_recognize_12.out[1])
}
"""

PARAMETERS_COMMON = {
    'params.mets_path': '"null"',
    'params.workspace_dir': '"null"',
    'params.pages': '"null"',
}

PARAMETERS_LOCAL = {
    'params.forks': '"4"',
}

PARAMETERS_DOCKER = {
    'params.forks': '"4"',
    'params.env_wrapper_cmd_core': '"null"',
    'params.env_wrapper_cmd_step0': '"null"',
    'params.env_wrapper_cmd_step1': '"null"',
    'params.env_wrapper_cmd_step2': '"null"',
}

PARAMETERS_APPTAINER = {
    'params.cpus': '"null"',
    'params.ram': '"null"',
    'params.forks': 'params.cpus',
    'params.cpus_per_fork': '(params.cpus.toInteger() / params.forks.toInteger()).intValue()',
    'params.ram_per_fork': 'sprintf("%dGB", (params.ram.toInteger() / params.forks.toInteger()).intValue())',
    'params.env_wrapper_cmd_core': '"null"',
    'params.env_wrapper_cmd_step0': '"null"',
    'params.env_wrapper_cmd_step1': '"null"',
    'params.env_wrapper_cmd_step2': '"null"',
}
