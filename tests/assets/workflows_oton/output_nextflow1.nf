nextflow.enable.dsl = 2

params.mets_path = "null"
params.input_file_grp = "OCR-D-IMG"

process ocrd_cis_ocropy_binarize_0 {
    maxForks 1

    input:
        path mets_file
        val input_file_grp
        val output_file_grp

    output:
        path mets_file

    script:
        """
        ocrd-cis-ocropy-binarize -m ${mets_file} -I ${input_file_grp} -O ${output_file_grp}
        """
}

process ocrd_anybaseocr_crop_1 {
    maxForks 1

    input:
        path mets_file
        val input_file_grp
        val output_file_grp

    output:
        path mets_file

    script:
        """
        ocrd-anybaseocr-crop -m ${mets_file} -I ${input_file_grp} -O ${output_file_grp}
        """
}

process ocrd_skimage_binarize_2 {
    maxForks 1

    input:
        path mets_file
        val input_file_grp
        val output_file_grp

    output:
        path mets_file

    script:
        """
        ocrd-skimage-binarize -m ${mets_file} -I ${input_file_grp} -O ${output_file_grp} -p '{"method": "li"}'
        """
}

process ocrd_skimage_denoise_3 {
    maxForks 1

    input:
        path mets_file
        val input_file_grp
        val output_file_grp

    output:
        path mets_file

    script:
        """
        ocrd-skimage-denoise -m ${mets_file} -I ${input_file_grp} -O ${output_file_grp} -p '{"level-of-operation": "page"}'
        """
}

process ocrd_tesserocr_deskew_4 {
    maxForks 1

    input:
        path mets_file
        val input_file_grp
        val output_file_grp

    output:
        path mets_file

    script:
        """
        ocrd-tesserocr-deskew -m ${mets_file} -I ${input_file_grp} -O ${output_file_grp} -p '{"operation_level": "page"}'
        """
}

process ocrd_cis_ocropy_segment_5 {
    maxForks 1

    input:
        path mets_file
        val input_file_grp
        val output_file_grp

    output:
        path mets_file

    script:
        """
        ocrd-cis-ocropy-segment -m ${mets_file} -I ${input_file_grp} -O ${output_file_grp} -p '{"level-of-operation": "page"}'
        """
}

process ocrd_cis_ocropy_dewarp_6 {
    maxForks 1

    input:
        path mets_file
        val input_file_grp
        val output_file_grp

    output:
        path mets_file

    script:
        """
        ocrd-cis-ocropy-dewarp -m ${mets_file} -I ${input_file_grp} -O ${output_file_grp}
        """
}

process ocrd_calamari_recognize_7 {
    maxForks 1

    input:
        path mets_file
        val input_file_grp
        val output_file_grp

    output:
        path mets_file

    script:
        """
        ocrd-calamari-recognize -m ${mets_file} -I ${input_file_grp} -O ${output_file_grp} -p '{"checkpoint_dir": "qurator-gt4histocr-1.0"}'
        """
}

workflow {
    main:
        ocrd_cis_ocropy_binarize_0(params.mets_path, params.input_file_grp, "OCR-D-BIN")
        ocrd_anybaseocr_crop_1(ocrd_cis_ocropy_binarize_0.out, "OCR-D-BIN", "OCR-D-CROP")
        ocrd_skimage_binarize_2(ocrd_anybaseocr_crop_1.out, "OCR-D-CROP", "OCR-D-BIN2")
        ocrd_skimage_denoise_3(ocrd_skimage_binarize_2.out, "OCR-D-BIN2", "OCR-D-BIN-DENOISE")
        ocrd_tesserocr_deskew_4(ocrd_skimage_denoise_3.out, "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
        ocrd_cis_ocropy_segment_5(ocrd_tesserocr_deskew_4.out, "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG")
        ocrd_cis_ocropy_dewarp_6(ocrd_cis_ocropy_segment_5.out, "OCR-D-SEG", "OCR-D-SEG-LINE-RESEG-DEWARP")
        ocrd_calamari_recognize_7(ocrd_cis_ocropy_dewarp_6.out, "OCR-D-SEG-LINE-RESEG-DEWARP", "OCR-D-OCR")
}
