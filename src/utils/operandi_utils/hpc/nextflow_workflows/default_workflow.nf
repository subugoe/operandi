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
    OPERANDI - HPC - Default Workflow
    ===========================================
    input_file_group    : ${params.input_file_group}
    mets                : ${params.mets}
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

process ocrd_cis_ocropy_binarize {
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
    ${params.singularity_wrapper} ocrd-cis-ocropy-binarize -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group}
    """
}

process ocrd_anybaseocr_crop {
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
    ${params.singularity_wrapper} ocrd-anybaseocr-crop -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group}
    """
}

process ocrd_skimage_binarize {
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
    ${params.singularity_wrapper} ocrd-skimage-binarize -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -p '{"method": "li"}'
    """
}

process ocrd_skimage_denoise {
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
    ${params.singularity_wrapper} ocrd-skimage-denoise -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -p '{"level-of-operation": "page"}'
    """
}

process ocrd_tesserocr_deskew {
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
    ${params.singularity_wrapper} ocrd-tesserocr-deskew -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -p '{"operation_level": "page"}'
    """
}

process ocrd_cis_ocropy_segment {
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
    ${params.singularity_wrapper} ocrd-cis-ocropy-segment -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -p '{"level-of-operation": "page"}'
    """
}

process ocrd_cis_ocropy_dewarp {
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

process ocrd_calamari_recognize {
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
    ${params.singularity_wrapper} ocrd-calamari-recognize -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -p '{"checkpoint_dir": "qurator-gt4histocr-1.0"}'
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
        ocrd_cis_ocropy_binarize(split_page_ranges.out[0], split_page_ranges.out[1], params.input_file_group, "OCR-D-BIN")
        ocrd_anybaseocr_crop(ocrd_cis_ocropy_binarize.out[0], ocrd_cis_ocropy_binarize.out[1], "OCR-D-BIN", "OCR-D-CROP")
        ocrd_skimage_binarize(ocrd_anybaseocr_crop.out[0], ocrd_anybaseocr_crop.out[1], "OCR-D-CROP", "OCR-D-BIN2")
        ocrd_skimage_denoise(ocrd_skimage_binarize.out[0], ocrd_skimage_binarize.out[1], "OCR-D-BIN2", "OCR-D-BIN-DENOISE")
        ocrd_tesserocr_deskew(ocrd_skimage_denoise.out[0], ocrd_skimage_denoise.out[1], "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
        ocrd_cis_ocropy_segment(ocrd_tesserocr_deskew.out[0], ocrd_tesserocr_deskew.out[1], "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG")
        ocrd_cis_ocropy_dewarp(ocrd_cis_ocropy_segment.out[0], ocrd_cis_ocropy_segment.out[1], "OCR-D-SEG", "OCR-D-SEG-LINE-RESEG-DEWARP")
        ocrd_calamari_recognize(ocrd_cis_ocropy_dewarp.out[0], ocrd_cis_ocropy_dewarp.out[1], "OCR-D-SEG-LINE-RESEG-DEWARP", "OCR-D-OCR")
        merging_mets(ocrd_calamari_recognize.out[0], ocrd_calamari_recognize.out[1])
}
