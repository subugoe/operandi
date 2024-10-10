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
    OPERANDI - HPC - SBB Workflow
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

process ocrd_tesserocr_recognize {
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
    ${params.singularity_wrapper} tesserocr-recognize -w ${params.workspace_dir} -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group} -P segmentation_level region -P textequiv_level word -P find_tables true -P model deu
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
        ocrd_tesserocr_recognize(split_page_ranges.out[0], split_page_ranges.out[1], params.input_file_group, "OCR-D-OCR")
        merging_mets(ocrd_tesserocr_recognize.out[0], ocrd_tesserocr_recognize.out[1])
}
