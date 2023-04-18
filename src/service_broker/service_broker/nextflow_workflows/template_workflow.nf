nextflow.enable.dsl=2

// The values are assigned inside the batch script
// Based on internal values and options provided in the request
params.input_file_group = "null"
params.mets = "null"
params.volume_map_dir = "null"
params.sif_path = "null"

log.info """\
         O P E R A N D I - H P C - T E S T  P I P E L I N E
         ===========================================
         volume_map_dir   : ${params.volume_map_dir}
         sif_path         : ${params.sif_path}
         mets             : ${params.mets}
         input_file_group : ${params.input_file_group}
         """
         .stripIndent()

process ocrd_cis_ocropy_binarize {
  maxForks 1
  echo true

  input:
    path mets_file
    val input_group

  script:
  """
  singularity exec --bind ${params.volume_map_dir} ${params.sif_path} ocrd-cis-ocropy-binarize -m ${mets_file} -I ${input_group} -O "OCR-D-BIN"
  """
}

workflow {
  main:
    ocrd_cis_ocropy_binarize(params.mets, params.input_file_group)
}