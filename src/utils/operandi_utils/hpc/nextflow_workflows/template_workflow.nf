nextflow.enable.dsl=2

// The values are assigned inside the batch script
// Based on internal values and options provided in the request
params.input_file_group = "null"
params.mets = "null"
params.singularity_wrapper = "null"
params.cpus = "null"

log.info """\
         O P E R A N D I - H P C - T E S T  P I P E L I N E
         ===========================================
         input_file_group    : ${params.input_file_group}
         mets                : ${params.mets}
         singularity_wrapper : ${params.singularity_wrapper}
         cpus                : ${params.cpu}
         """
         .stripIndent()

process ocrd_cis_ocropy_binarize {
  maxForks 1
  cpus params.cpus
  echo true

  input:
    path mets_file
    val input_group

  script:
  """
  ${params.singularity_wrapper} ocrd-cis-ocropy-binarize -m ${mets_file} -I ${input_group} -O "OCR-D-BIN"
  """
}

workflow {
  main:
    ocrd_cis_ocropy_binarize(params.mets, params.input_file_group)
}
