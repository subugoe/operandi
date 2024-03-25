nextflow.enable.dsl=2

// The values are assigned inside the batch script
// Based on internal values and options provided in the request
params.input_file_group = "null"
params.mets = "null"
params.workspace_dir = "null"
// amount of pages of the workspace
params.pages = "null"
params.singularity_wrapper = "null"
params.cpus = "null"
params.ram = "null"
params.forks = params.cpus
// Do not pass these parameters from the caller unless you know what you are doing
params.cpus_per_fork = (params.cpus.toInteger() / params.forks.toInteger()).intValue()
params.ram_per_fork = sprintf("%dGB", (params.ram.toInteger() / params.forks.toInteger()).intValue())

log.info """\
    OPERANDI - HPC - Odem Workflow
    ===========================================
    input_file_group    : ${params.input_file_group}
    mets                : ${params.mets}
    mets_socket         : ${params.mets_socket}
    workspace_dir       : ${params.workspace_dir}
    pages               : ${params.pages}
    singularity_wrapper : ${params.singularity_wrapper}
    cpus                : ${params.cpus}
    ram                 : ${params.ram}
    forks               : ${params.forks}
    cpus_per_fork       : ${params.cpus_per_fork}
    ram_per_fork        : ${params.ram_per_fork}
    """
    .stripIndent()

process split_page_ranges {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val range_multiplier
    output:
        env mets_file_chunk
        env current_range_pages
    script:
    """
    current_range_pages=\$(${params.singularity_wrapper} ocrd workspace -d ${params.workspace_dir} list-page -f comma-separated -D ${params.forks} -C ${range_multiplier})
    echo "Current range is: \$current_range_pages"
    mets_file_chunk=\$(echo ${params.workspace_dir}/mets_${range_multiplier}.xml)
    echo "Mets file chunk path: \$mets_file_chunk"
    \$(${params.singularity_wrapper} cp -p ${params.mets} \$mets_file_chunk)
    """
}

process ocrd_cis_ocropy_binarize_0 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val mets_file_chunk
        val page_range
        val input_group
        val output_group
    output:
        val mets_file_chunk
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-binarize -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -P dpi 300
    """
}

process ocrd_anybaseocr_crop_1 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val mets_file_chunk
        val page_range
        val input_group
        val output_group
    output:
        val mets_file_chunk
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-anybaseocr-crop -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -P dpi 300
    """
}

process ocrd_cis_ocropy_denoise_2 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val mets_file_chunk
        val page_range
        val input_group
        val output_group
    output:
        val mets_file_chunk
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-denoise -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -P dpi 300
    """
}

process ocrd_cis_ocropy_deskew_3 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val mets_file_chunk
        val page_range
        val input_group
        val output_group
    output:
        val mets_file_chunk
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-deskew -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -P level-of-operation page
    """
}

process ocrd_tesserocr_segment_region_4 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val mets_file_chunk
        val page_range
        val input_group
        val output_group
    output:
        val mets_file_chunk
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-tesserocr-segment-region -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -P padding 5.0 -P find_tables false -P dpi 300
    """
}

process ocrd_segment_repair_5 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val mets_file_chunk
        val page_range
        val input_group
        val output_group
    output:
        val mets_file_chunk
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-segment-repair -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -P plausibilize true -P plausibilize_merge_min_overlap 0.7
    """
}

process ocrd_cis_ocropy_clip_6 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val mets_file_chunk
        val page_range
        val input_group
        val output_group
    output:
        val mets_file_chunk
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-clip -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group}
    """
}

process ocrd_cis_ocropy_segment_7 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val mets_file_chunk
        val page_range
        val input_group
        val output_group
    output:
        val mets_file_chunk
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-segment -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -P dpi 300
    """
}

process ocrd_cis_ocropy_dewarp_8 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val mets_file_chunk
        val page_range
        val input_group
        val output_group
    output:
        val mets_file_chunk
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-dewarp -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group}
    """
}

process ocrd_tesserocr_recognize_9 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val mets_file_chunk
        val page_range
        val input_group
        val output_group
    output:
        val mets_file_chunk
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-tesserocr-recognize -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -P model Fraktur
    """
}

process merging_mets {
    // Must be a single instance - modifying the main mets file
    maxForks 1

    input:
        val mets_file_chunk
        val page_range
    script:
    """
    ${params.singularity_wrapper} ocrd workspace -d ${params.workspace_dir} merge --force --no-copy-files ${mets_file_chunk} --page-id ${page_range}
    ${params.singularity_wrapper} rm ${mets_file_chunk}
    """
}

workflow {
    main:
        ch_range_multipliers = Channel.of(0..params.forks.intValue()-1)
        split_page_ranges(ch_range_multipliers)
        ocrd_cis_ocropy_binarize_0(split_page_ranges.out[0], split_page_ranges.out[1], params.input_file_group, "OCR-D-BINPAGE")
        ocrd_anybaseocr_crop_1(ocrd_cis_ocropy_binarize_0.out[0], ocrd_cis_ocropy_binarize_0.out[1], "OCR-D-BINPAGE", "OCR-D-SEG-PAGE-ANYOCR")
        ocrd_cis_ocropy_denoise_2(ocrd_anybaseocr_crop_1.out[0], ocrd_anybaseocr_crop_1.out[1], "OCR-D-SEG-PAGE-ANYOCR", "OCR-D-DENOISE-OCROPY")
        ocrd_cis_ocropy_deskew_3(ocrd_cis_ocropy_denoise_2.out[0], ocrd_cis_ocropy_denoise_2.out[1], "OCR-D-DENOISE-OCROPY", "OCR-D-DESKEW-OCROPY")
        ocrd_tesserocr_segment_region_4(ocrd_cis_ocropy_deskew_3.out[0], ocrd_cis_ocropy_deskew_3.out[1], "OCR-D-DESKEW-OCROPY", "OCR-D-SEG-BLOCK-TESSERACT")
        ocrd_segment_repair_5(ocrd_tesserocr_segment_region_4.out[0], ocrd_tesserocr_segment_region_4.out[1], "OCR-D-SEG-BLOCK-TESSERACT", "OCR-D-SEGMENT-REPAIR")
        ocrd_cis_ocropy_clip_6(ocrd_segment_repair_5.out[0], ocrd_segment_repair_5.out[1], "OCR-D-SEGMENT-REPAIR", "OCR-D-CLIP")
        ocrd_cis_ocropy_segment_7(ocrd_cis_ocropy_clip_6.out[0], ocrd_cis_ocropy_clip_6.out[1], "OCR-D-CLIP", "OCR-D-SEGMENT-OCROPY")
        ocrd_cis_ocropy_dewarp_8(ocrd_cis_ocropy_segment_7.out[0], ocrd_cis_ocropy_segment_7.out[1], "OCR-D-SEGMENT-OCROPY", "OCR-D-DEWARP")
        ocrd_tesserocr_recognize_9(ocrd_cis_ocropy_dewarp_8.out[0], ocrd_cis_ocropy_dewarp_8.out[1], "OCR-D-DEWARP", "OCR-D-OCR")
        merging_mets(ocrd_tesserocr_recognize_9.out[0], ocrd_tesserocr_recognize_9.out[1])
}
