nextflow.enable.dsl=2

// The values are assigned inside the batch script
// Based on internal values and options provided in the request
params.input_file_group = "null"
params.mets = "null"
params.mets_socket = "null"
params.workspace_dir = "null"
params.singularity_wrapper = "null"
params.cpus = "null"
params.ram = "null"
// by default single instance of each OCR-D processor
params.forks = 1

log.info """\
         O P E R A N D I - H P C - T E M P L A T E   P I P E L I N E
         ===========================================
         input_file_group    : ${params.input_file_group}
         mets                : ${params.mets}
         singularity_wrapper : ${params.singularity_wrapper}
         cpus                : ${params.cpus}
         ram                 : ${params.ram}
         """
         .stripIndent()

process ocrd_cis_ocropy_binarize {
  maxForks params.forks
  cpus params.cpus
  memory params.ram
  echo true

  input:
    path mets_file
    val input_group

  script:
  """
  ${params.singularity_wrapper} ocrd-cis-ocropy-binarize -U ${params.mets_socket} -w ${params.workspace_dir} -m ${mets_file} -I ${input_group} -O OCR-D-BIN
  """
}

workflow {
  main:
    ocrd_cis_ocropy_binarize(params.mets, params.input_file_group)
}
