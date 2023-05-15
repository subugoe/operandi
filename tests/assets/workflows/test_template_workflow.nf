nextflow.enable.dsl=2

// The values are assigned inside the batch script
// Based on internal values and options provided in the request
params.input_file_group = "null"
params.mets = "null"
params.volume_map_dir = "null"
params.models_mapping = "null"
params.sif_path = "null"
params.singularity_wrapper = "singularity exec --bind ${params.volume_map_dir} --bind ${params.models_mapping} ${params.sif_path}"

log.info """\
         O P E R A N D I - H P C - TEMPLATE  P I P E L I N E
         ===========================================
         input_file_group    : ${params.input_file_group}
         mets                : ${params.mets}
         volume_map_dir      : ${params.volume_map_dir}
         models_mapping      : ${params.models_mapping}
         sif_path            : ${params.sif_path}
         singularity_wrapper : ${params.singularity_wrapper}
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
  ${params.singularity_wrapper} ocrd-cis-ocropy-binarize -m ${mets_file} -I ${input_group} -O "OCR-D-BIN"
  """
}

workflow {
  main:
    ocrd_cis_ocropy_binarize(params.mets, params.input_file_group)
}