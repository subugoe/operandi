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
params.cpus_per_fork = (params.cpus.toInteger() / params.forks.toInteger()).intValue()
params.ram_per_fork = sprintf("%dGB", (params.ram.toInteger() / params.forks.toInteger()).intValue())

log.info """\
    OPERANDI - HPC - Default Workflow with Mets Server
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
        env current_range_pages
    shell:
    '''
    current_range_pages=$(!{params.singularity_wrapper} ocrd workspace -d !{params.workspace_dir} list-page -f comma-separated -D !{params.forks} -C !{range_multiplier})
    echo "Current range is: $current_range_pages"
    '''
}

process ocrd_cis_ocropy_binarize {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-binarize -U ${params.mets_socket} -w ${params.workspace_dir} --page-id ${page_range} -m ${params.mets} -I ${input_group} -O ${output_group}
    """
}

process ocrd_anybaseocr_crop {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-anybaseocr-crop -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group}
    """
}

process ocrd_skimage_binarize {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-skimage-binarize -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group} -p '{"method": "li"}'
    """
}

process ocrd_skimage_denoise {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-skimage-denoise -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group} -p '{"level-of-operation": "page"}'
    """
}

process ocrd_tesserocr_deskew {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-tesserocr-deskew -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group} -p '{"operation_level": "page"}'
    """
}

process ocrd_cis_ocropy_segment {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-segment -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group} -p '{"level-of-operation": "page"}'
    """
}

process ocrd_cis_ocropy_dewarp {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

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

process ocrd_calamari_recognize {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        val page_range
        val input_group
        val output_group
    output:
        val page_range

    script:
    """
    ${params.singularity_wrapper} ocrd-calamari-recognize -U ${params.mets_socket} -w ${params.workspace_dir} -m ${params.mets} --page-id ${page_range} -I ${input_group} -O ${output_group} -p '{"checkpoint_dir": "qurator-gt4histocr-1.0"}'
    """
}

workflow {
    main:
        ch_range_multipliers = Channel.of(0..params.forks.intValue()-1)
        split_page_ranges(ch_range_multipliers)
        ocrd_cis_ocropy_binarize(split_page_ranges.out, params.input_file_group, "OCR-D-BIN")
        ocrd_anybaseocr_crop(ocrd_cis_ocropy_binarize.out, "OCR-D-BIN", "OCR-D-CROP")
        ocrd_skimage_binarize(ocrd_anybaseocr_crop.out, "OCR-D-CROP", "OCR-D-BIN2")
        ocrd_skimage_denoise(ocrd_skimage_binarize.out, "OCR-D-BIN2", "OCR-D-BIN-DENOISE")
        ocrd_tesserocr_deskew(ocrd_skimage_denoise.out, "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
        ocrd_cis_ocropy_segment(ocrd_tesserocr_deskew.out, "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG")
        ocrd_cis_ocropy_dewarp(ocrd_cis_ocropy_segment.out, "OCR-D-SEG", "OCR-D-SEG-LINE-RESEG-DEWARP")
        ocrd_calamari_recognize(ocrd_cis_ocropy_dewarp.out, "OCR-D-SEG-LINE-RESEG-DEWARP", "OCR-D-OCR")
}
