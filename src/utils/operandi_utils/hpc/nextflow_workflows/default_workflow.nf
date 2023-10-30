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
         O P E R A N D I - H P C - D E F A U L T  P I P E L I N E
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
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-cis-ocropy-binarize -U ${params.mets_socket} -w ${params.workspace_dir} -m ${mets_file} -I ${input_group} -O ${output_group}
  """
}

process ocrd_anybaseocr_crop {
  maxForks params.forks
  cpus params.cpus
  memory params.ram
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-anybaseocr-crop -U ${params.mets_socket} -w ${params.workspace_dir} -m ${mets_file} -I ${input_group} -O ${output_group}
  """
}

process ocrd_skimage_binarize {
  maxForks params.forks
  cpus params.cpus
  memory params.ram
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-skimage-binarize -U ${params.mets_socket} -w ${params.workspace_dir} -m ${mets_file} -I ${input_group} -O ${output_group} -p '{"method": "li"}'
  """
}

process ocrd_skimage_denoise {
  maxForks params.forks
  cpus params.cpus
  memory params.ram
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-skimage-denoise -U ${params.mets_socket} -w ${params.workspace_dir} -m ${mets_file} -I ${input_group} -O ${output_group} -p '{"level-of-operation": "page"}'
  """
}

process ocrd_tesserocr_deskew {
  maxForks params.forks
  cpus params.cpus
  memory params.ram
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-tesserocr-deskew -U ${params.mets_socket} -w ${params.workspace_dir} -m ${mets_file} -I ${input_group} -O ${output_group} -p '{"operation_level": "page"}'
  """
}

process ocrd_cis_ocropy_segment {
  maxForks params.forks
  cpus params.cpus
  memory params.ram
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-cis-ocropy-segment -U ${params.mets_socket} -w ${params.workspace_dir} -m ${mets_file} -I ${input_group} -O ${output_group} -p '{"level-of-operation": "page"}'
  """
}

process ocrd_cis_ocropy_dewarp {
  maxForks params.forks
  cpus params.cpus
  memory params.ram
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-cis-ocropy-dewarp -U ${params.mets_socket} -w ${params.workspace_dir} -m ${mets_file} -I ${input_group} -O ${output_group}
  """
}

process ocrd_calamari_recognize {
  maxForks params.forks
  cpus params.cpus
  memory params.ram
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-calamari-recognize -U ${params.mets_socket} -w ${params.workspace_dir} -m ${mets_file} -I ${input_group} -O ${output_group} -p '{"checkpoint_dir": "qurator-gt4histocr-1.0"}'
  """
}


workflow {
  main:
    ocrd_cis_ocropy_binarize(params.mets, params.input_file_group, "OCR-D-BIN")
    ocrd_anybaseocr_crop(ocrd_cis_ocropy_binarize.out, "OCR-D-BIN", "OCR-D-CROP")
    ocrd_skimage_binarize(ocrd_anybaseocr_crop.out, "OCR-D-CROP", "OCR-D-BIN2")
    ocrd_skimage_denoise(ocrd_skimage_binarize.out, "OCR-D-BIN2", "OCR-D-BIN-DENOISE")
    ocrd_tesserocr_deskew(ocrd_skimage_denoise.out, "OCR-D-BIN-DENOISE", "OCR-D-BIN-DENOISE-DESKEW")
    ocrd_cis_ocropy_segment(ocrd_tesserocr_deskew.out, "OCR-D-BIN-DENOISE-DESKEW", "OCR-D-SEG")
    ocrd_cis_ocropy_dewarp(ocrd_cis_ocropy_segment.out, "OCR-D-SEG", "OCR-D-SEG-LINE-RESEG-DEWARP")
    ocrd_calamari_recognize(ocrd_cis_ocropy_dewarp.out, "OCR-D-SEG-LINE-RESEG-DEWARP", "OCR-D-OCR")
}
