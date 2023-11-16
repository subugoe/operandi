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
// by default single instance of each OCR-D processor
params.forks = 2
params.pages_per_range = params.pages / params.forks

log.info """\
         O P E R A N D I - H P C - T E M P L A T E   P I P E L I N E
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
         """
         .stripIndent()

process split_page_ranges {
    maxForks 1
    cpus params.cpus
    memory params.ram

    input:
        val range_multiplier
    output:
        val current_range_pages
    exec:
        range_start = 1 + params.pages_per_range * range_multiplier
        range_end = range_start + params.pages_per_range - 1
        // Works only for workspaces with regular page_id ranges
        start = sprintf("PHYS_%04d", range_start.intValue())
        end = sprintf("PHYS_%04d", range_end.intValue())
        current_range_pages = start + ".." + end
}

process ocrd_cis_ocropy_binarize {
    maxForks params.forks
    cpus params.cpus
    memory params.ram
    debug true

    input:
        val page_range
        path mets_file
        val input_group
        val output_group
    script:
    """
    ${params.singularity_wrapper} ocrd-cis-ocropy-binarize -U ${params.mets_socket} -w ${params.workspace_dir} -m ${mets_file} --page-id ${page_range} -I ${input_group} -O ${output_group}
    """
}

workflow {
    main:
        ch_range_multipliers = Channel.of(0..params.forks-1)
        split_page_ranges(ch_range_multipliers)
        ocrd_cis_ocropy_binarize(split_page_ranges.out[0], params.mets, params.input_file_group, "OCR-D-BIN")
}
