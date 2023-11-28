nextflow.enable.dsl=2

// The values are assigned inside the batch script
// Based on internal values and options provided in the request
params.input_file_group = "null"
params.mets = "null"
params.mets_socket = "null"
params.workspace_dir = "null"
// amount of pages of the workspace
params.pages = "null"
params.singularity_wrapper = "null"
params.cpus = "null"
params.ram = "null"
params.forks = params.cpus
// Do not pass these parameters from the caller unless you know what you are doing
params.pages_per_range = Math.round(params.pages.toInteger() / params.forks.toInteger()).intValue()
params.cpus_per_fork = (params.cpus.toInteger() / params.forks.toInteger()).intValue()
params.ram_per_fork = sprintf("%dGB", (params.ram.toInteger() / params.forks.toInteger()).intValue())

log.info """\
         O P E R A N D I - H P C - WORKFLOW ODEM
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
         pages_per_range     : ${params.pages_per_range}
         cpus_per_fork       : ${params.cpus_per_fork}
         ram_per_fork        : ${params.ram_per_fork}
         """
         .stripIndent()

process split_page_ranges {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork

    input:
        val range_multiplier
    output:
        val current_range_pages
    exec:
        range_start = (1 + params.pages_per_range * range_multiplier).intValue()
        range_end = (range_start + params.pages_per_range - 1).intValue()
        pages_int = params.pages.toInteger()
        // Prevent range overflow
        if(range_end > pages_int){
            range_end = pages_int
        }
        // Prevent last pages being left out
        pages_left = pages_int - range_end
        if(pages_left < params.pages_per_range){
            range_end = range_end + pages_left
        }
        // Works only for workspaces with regular page_id ranges
        start = sprintf("PHYS_%04d", range_start)
        end = sprintf("PHYS_%04d", range_end)
        current_range_pages = start + ".." + end
        println("Current page range: ${current_range_pages}")
}

process ocrd_cis_ocropy_binarize_0 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    echo true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-binarize -U ${params.mets_socket} -w ${params.workspace_dir} --page-id ${page_range} -m ${params.mets} -I ${input_group} -O ${output_group} -P dpi 300
    """
}

process ocrd_anybaseocr_crop_1 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    echo true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-anybaseocr-crop -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group} -P dpi 300
    """
}

process ocrd_cis_ocropy_denoise_2 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    echo true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-denoise -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group} -P dpi 300
    """
}

process ocrd_cis_ocropy_deskew_3 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    echo true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-deskew -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group} -P level-of-operation page
    """
}

process ocrd_tesserocr_segment_region_4 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    echo true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-tesserocr-segment-region -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group} -P padding 5.0 -P find_tables false -P dpi 300
    """
}

process ocrd_segment_repair_5 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    echo true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-segment-repair -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group} -P plausibilize true -P plausibilize_merge_min_overlap 0.7
    """
}

process ocrd_cis_ocropy_clip_6 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    echo true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-clip -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group}
    """
}

process ocrd_cis_ocropy_segment_7 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    echo true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-segment -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group} -P dpi 300
    """
}

process ocrd_cis_ocropy_dewarp_8 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    echo true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-dewarp -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group}
    """
}

process ocrd_tesserocr_recognize_9 {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    echo true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-tesserocr-recognize -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group} -P model Fraktur
    """
}

workflow {
    main:
        ch_range_multipliers = Channel.of(0..params.forks.intValue()-1)
        split_page_ranges(ch_range_multipliers)
        ocrd_cis_ocropy_binarize_0(split_page_ranges.out, params.input_file_group, "OCR-D-BINPAGE")
        ocrd_anybaseocr_crop_1(ocrd_cis_ocropy_binarize_0.out, "OCR-D-BINPAGE", "OCR-D-SEG-PAGE-ANYOCR")
        ocrd_cis_ocropy_denoise_2(ocrd_anybaseocr_crop_1.out, "OCR-D-SEG-PAGE-ANYOCR", "OCR-D-DENOISE-OCROPY")
        ocrd_cis_ocropy_deskew_3(ocrd_cis_ocropy_denoise_2.out, "OCR-D-DENOISE-OCROPY", "OCR-D-DESKEW-OCROPY")
        ocrd_tesserocr_segment_region_4(ocrd_cis_ocropy_deskew_3.out, "OCR-D-DESKEW-OCROPY", "OCR-D-SEG-BLOCK-TESSERACT")
        ocrd_segment_repair_5(ocrd_tesserocr_segment_region_4.out, "OCR-D-SEG-BLOCK-TESSERACT", "OCR-D-SEGMENT-REPAIR")
        ocrd_cis_ocropy_clip_6(ocrd_segment_repair_5.out, "OCR-D-SEGMENT-REPAIR", "OCR-D-CLIP")
        ocrd_cis_ocropy_segment_7(ocrd_cis_ocropy_clip_6.out, "OCR-D-CLIP", "OCR-D-SEGMENT-OCROPY")
        ocrd_cis_ocropy_dewarp_8(ocrd_cis_ocropy_segment_7.out, "OCR-D-SEGMENT-OCROPY", "OCR-D-DEWARP")
        ocrd_tesserocr_recognize_9(ocrd_cis_ocropy_dewarp_8.out, "OCR-D-DEWARP", "OCR-D-OCR")
}
