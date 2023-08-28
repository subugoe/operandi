nextflow.enable.dsl=2

// The values are assigned inside the batch script
// Based on internal values and options provided in the request
params.input_file_group = "null"
params.workspace_dir = "null"
params.mets = "null"
params.volume_map_dir = "null"
params.models_mapping = "null"
params.sif_path = "null"
params.singularity_wrapper = "singularity exec --bind ${params.volume_map_dir} --env OCRD_METS_CACHING=true ${params.sif_path}"
params.cpus = "null"

log.info """\
         O P E R A N D I - H P C - T E S T  P I P E L I N E
         ===========================================
         input_file_group    : ${params.input_file_group}
         workspace_dir       : ${params.workspace_dir}
         mets                : ${params.mets}
         volume_map_dir      : ${params.volume_map_dir}
         models_mapping      : ${params.models_mapping}
         sif_path            : ${params.sif_path}
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
