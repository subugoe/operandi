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
    OPERANDI - HPC - Template Workflow with Mets Server
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
        val "${params.workspace_dir}/mets_${range_multiplier}.xml"
        env current_range_pages
    shell:
    '''
    current_range_pages=$(!{params.singularity_wrapper} ocrd workspace -d !{params.workspace_dir} list-page -f comma-separated -D !{params.forks} -C !{range_multiplier})
    echo "Current range is: $current_range_pages"
    // Create a duplicate mets file and set the name according to the range multiplier
    cp !{params.mets} !{params.workspace_dir}/mets_!{range_multiplier}.xml
    '''
}

process ocrd_cis_ocropy_binarize {
    maxForks params.forks
    cpus params.cpus_per_fork
    memory params.ram_per_fork
    debug true

    input:
        path mets_file_chunk
        val page_range
        val input_group
        val output_group
    output:
        path mets_file_chunk
        val page_range
    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-binarize -m ${mets_file_chunk} --page-id ${page_range} -I ${input_group} -O ${output_group}
    """
}

process merging_mets {
    // Must be a single instance - modifying the main mets file
    maxForks 1

    input:
        path mets_file_chunk
        val page_range
    script:
    """
    ${params.singularity_wrapper} ocrd workspace --mets ${params.mets} merge --force --no-copy-files ${mets_file_chunk} --page-id ${page_range}
    // rm ${mets_file_chunk}
    """
}

workflow {
    main:
        ch_range_multipliers = Channel.of(0..params.forks.intValue()-1)
        split_page_ranges(ch_range_multipliers)
        ocrd_cis_ocropy_binarize(split_page_ranges.out[0], split_page_ranges.out[1], params.input_file_group, "OCR-D-BIN")
        merging_mets(ocrd_cis_ocropy_binarize.out[0], ocrd_cis_ocropy_binarize.out[1])
}
