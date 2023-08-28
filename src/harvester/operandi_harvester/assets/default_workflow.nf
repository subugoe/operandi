nextflow.enable.dsl=2

// The values are assigned inside the batch script
// Based on internal values and options provided in the request
params.input_file_group = "null"
params.mets = "null"
params.volume_map_dir = "null"
params.models_mapping = "null"
params.sif_path = "null"
params.singularity_wrapper = "singularity exec --bind ${params.volume_map_dir} --bind ${params.models_mapping} --env OCRD_METS_CACHING=true ${params.sif_path}"
params.cpus = "null"

log.info """\
         O P E R A N D I - H P C - D E F A U L T  P I P E L I N E
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
  params.cpus
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-cis-ocropy-binarize -m ${mets_file} -I ${input_group} -O ${output_group}
  """
}

process ocrd_anybaseocr_crop {
  maxForks 1
  params.cpus
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-anybaseocr-crop -m ${mets_file} -I ${input_group} -O ${output_group}
  """
}

process ocrd_skimage_binarize {
  maxForks 1
  params.cpus
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-skimage-binarize -m ${mets_file} -I ${input_group} -O ${output_group} -p '{"method": "li"}'
  """
}

process ocrd_skimage_denoise {
  maxForks 1
  params.cpus
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-skimage-denoise -m ${mets_file} -I ${input_group} -O ${output_group} -p '{"level-of-operation": "page"}'
  """
}

process ocrd_tesserocr_deskew {
  maxForks 1
  params.cpus
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-tesserocr-deskew -m ${mets_file} -I ${input_group} -O ${output_group} -p '{"operation_level": "page"}'
  """
}

process ocrd_cis_ocropy_segment {
  maxForks 1
  params.cpus
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-cis-ocropy-segment -m ${mets_file} -I ${input_group} -O ${output_group} -p '{"level-of-operation": "page"}'
  """
}

process ocrd_cis_ocropy_dewarp {
  maxForks 1
  params.cpus
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-cis-ocropy-dewarp -m ${mets_file} -I ${input_group} -O ${output_group}
  """
}

process ocrd_calamari_recognize {
  maxForks 1
  params.cpus
  echo true

  input:
    path mets_file
    val input_group
    val output_group

  output:
    path mets_file

  script:
  """
  ${params.singularity_wrapper} ocrd-calamari-recognize -m ${mets_file} -I ${input_group} -O ${output_group} -p '{"checkpoint_dir": "qurator-gt4histocr-1.0"}'
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
