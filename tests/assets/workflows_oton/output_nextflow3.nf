nextflow.enable.dsl = 2

params.mets_path = "null"
params.input_file_grp = "OCR-D-GT-SEG-BLOCK,OCR-D-OCR"

process ocrd_dinglehopper_0 {
    maxForks 1

    input:
        path mets_file
        val input_file_grp
        val output_file_grp

    output:
        path mets_file

    script:
        """
        ocrd-dinglehopper -m ${mets_file} -I ${input_file_grp} -O ${output_file_grp}
        """
}

process ocrd_dinglehopper_1 {
    maxForks 1

    input:
        path mets_file
        val input_file_grp
        val output_file_grp

    output:
        path mets_file

    script:
        """
        ocrd-dinglehopper -m ${mets_file} -I ${input_file_grp} -O ${output_file_grp}
        """
}

process ocrd_dinglehopper_2 {
    maxForks 1

    input:
        path mets_file
        val input_file_grp
        val output_file_grp

    output:
        path mets_file

    script:
        """
        ocrd-dinglehopper -m ${mets_file} -I ${input_file_grp} -O ${output_file_grp}
        """
}

workflow {
    main:
        ocrd_dinglehopper_0(params.mets_path, params.input_file_grp, "OCR-D-EVAL-SEG-BLOCK")
        ocrd_dinglehopper_1(ocrd_dinglehopper_0.out, "OCR-D-GT-SEG-LINE,OCR-D-OCR", "OCR-D-EVAL-SEG-LINE")
        ocrd_dinglehopper_2(ocrd_dinglehopper_1.out, "OCR-D-GT-SEG-PAGE,OCR-D-OCR", "OCR-D-EVAL-SEG-PAGE")
}
