nextflow.enable.dsl=2

// pipeline parameters
params.venv_path = "\$HOME/venv37-ocrd/bin/activate"
params.file_group = "PRESENTATION"
params.workspace = "$projectDir/ocrd-workspace"
params.mets = "${params.workspace}/mets.xml"
params.reads = "${params.workspace}/${params.file_group}"
params.cleaning = "OFF" // nextflow run <script> --cleaning "ON"/"OFF"

// log pipeline parameters to the console
log.info """\
  O C R - D - W O R K F L O W 2 - Serial
  ======================================================
  environment       : ${params.venv_path}
  workpace          : ${params.workspace}
  mets              : ${params.mets}
  file_group        : ${params.file_group}
  cleaning          : ${params.cleaning}

  OCR-D WORKFLOW REPRESENTED WITH THIS NEXTFLOW SCRIPT:
  ======================================================
  ocrd process \\
  "olena-binarize -I OCR-D-IMG -O OCR-D-BIN -P impl sauvola" \\
  "anybaseocr-crop -I OCR-D-BIN -O OCR-D-CROP" \\
  "olena-binarize -I OCR-D-CROP -O OCR-D-BIN2 -P impl kim" \\
  "cis-ocropy-denoise -I OCR-D-BIN2 -O OCR-D-BIN-DENOISE -P level-of-operation page" \\
  "cis-ocropy-deskew -I OCR-D-BIN-DENOISE -O OCR-D-BIN-DENOISE-DESKEW -P level-of-operation page" \\
  "tesserocr-segment-region -I OCR-D-BIN-DENOISE-DESKEW -O OCR-D-SEG-REG" \\
  "segment-repair -I OCR-D-SEG-REG -O OCR-D-SEG-REPAIR -P plausibilize true" \\
  "cis-ocropy-deskew -I OCR-D-SEG-REPAIR -O OCR-D-SEG-REG-DESKEW -P level-of-operation region" \\
  "cis-ocropy-clip -I OCR-D-SEG-REG-DESKEW -O OCR-D-SEG-REG-DESKEW-CLIP -P level-of-operation region" \\
  "tesserocr-segment-line -I OCR-D-SEG-REG-DESKEW-CLIP -O OCR-D-SEG-LINE" \\
  "segment-repair -I OCR-D-SEG-LINE -O OCR-D-SEG-REPAIR-LINE -P sanitize true" \\
  "cis-ocropy-dewarp -I OCR-D-SEG-REPAIR-LINE -O OCR-D-SEG-LINE-RESEG-DEWARP" \\
  "calamari-recognize -I OCR-D-SEG-LINE-RESEG-DEWARP -O OCR-D-OCR -P checkpoint_dir qurator-gt4histocr-1.0"
  ======================================================
  """
  .stripIndent()

process cleaning_mets {
  echo true

  input:
    path mets_file

  output:
    path mets_file

  script:
  if (params.cleaning == "ON")
    """
    source "${params.venv_path}"
    echo "Cleaning of unnecessary file groups is turned on"
    ocrd workspace --mets ${mets_file} remove-group --recursive --force MIN
    echo "MIN fileGrp was removed from the mets file"
    ocrd workspace --mets ${mets_file} remove-group --recursive --force DEFAULT
    echo "DEFAULT fileGrp was removed from the mets file"
    ocrd workspace --mets ${mets_file} remove-group --recursive --force THUMBS
    echo "THUMBS fileGrp was removed from the mets file"
    ocrd workspace --mets ${mets_file} remove-group --recursive --force MAX
    echo "MAX fileGrp was removed from the mets file"
    deactivate
    """
  else
    """
    echo "Cleaning of unnecessary file groups is turned off"
    """
}

process olena_binarize_sauvola {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir

  script:
    """
    source "${params.venv_path}"
    ocrd-olena-binarize --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P impl sauvola
    deactivate
    """
}

process anybaseocr_crop {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir

  script:
    """
    source "${params.venv_path}"
    ocrd-anybaseocr-crop --mets ${mets_file} -I ${input_dir} -O ${output_dir}
    deactivate
    """
}

process olena_binarize_kim {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir

  script:
    """
    source "${params.venv_path}"
    ocrd-olena-binarize --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P impl kim
    deactivate
    """
}

process ocropy_denoise {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-denoise --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P level-of-operation page
    deactivate
    """ 
}

process ocropy_deskew_page {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-deskew --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P operation_level page
    deactivate
    """ 
}

process tesserocr_segment_region {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-tesserocr-segment-region --mets ${mets_file} -I ${input_dir} -O ${output_dir}
    deactivate
    """ 
}

process segment_repair_plausibilized {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-segment-repair --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P plausibilize true
    deactivate
    """ 
}

process ocropy_deskew_region {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-deskew --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P operation_level region
    deactivate
    """ 
}

process ocropy_clip {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-clip --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P operation_level region
    deactivate
    """ 
}

process tesserocr_segment_line {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-tesserocr-segment-line --mets ${mets_file} -I ${input_dir} -O ${output_dir}
    deactivate
    """ 
}

process segment_repair_sanitized {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-segment-repair --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P sanitize true
    deactivate
    """ 
}

process ocropy_dewarp {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-dewarp --mets ${mets_file} -I ${input_dir} -O ${output_dir}
    deactivate
    """   
}

process calamari_recognize {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir

  script:
    """
    source "${params.venv_path}"
    ocrd-calamari-recognize --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P checkpoint_dir qurator-gt4histocr-1.0
    deactivate
    """
}

// This is the main workflow
workflow {
  main:
    // Cleaning the mets if turned on
    cleaning_mets(params.mets)

    // OCR-D workflow processes
    olena_binarize_sauvola(cleaning_mets.out[0], params.file_group, "OCR-D-BIN")
    anybaseocr_crop(cleaning_mets.out[0], olena_binarize_sauvola.out[0], "OCR-D-CROP")
    olena_binarize_kim(cleaning_mets.out[0], anybaseocr_crop.out[0], "OCR-D-BIN2")
    ocropy_denoise(cleaning_mets.out[0], olena_binarize_kim.out[0], "OCR-D-BIN-DENOISE")
    ocropy_deskew_page(cleaning_mets.out[0], ocropy_denoise.out[0], "OCR-D-BIN-DENOISE-DESKEW")
    tesserocr_segment_region(cleaning_mets.out[0], ocropy_deskew_page.out[0], "OCR-D-SEG-REG")
    segment_repair_plausibilized(cleaning_mets.out[0], tesserocr_segment_region.out[0], "OCR-D-SEG-REPAIR")
    ocropy_deskew_region(cleaning_mets.out[0], segment_repair_plausibilized.out[0], "OCR-D-SEG-REG-DESKEW")
    ocropy_clip(cleaning_mets.out[0], ocropy_deskew_region.out[0], "OCR-D-SEG-REG-DESKEW-CLIP")
    tesserocr_segment_line(cleaning_mets.out[0], ocropy_clip.out[0], "OCR-D-SEG-LINE")
    segment_repair_sanitized(cleaning_mets.out[0], tesserocr_segment_line.out[0], "OCR-D-SEG-REPAIR-LINE")
    ocropy_dewarp(cleaning_mets.out[0], segment_repair_sanitized.out[0], "OCR-D-SEG-LINE-RESEG-DEWARP")
    calamari_recognize(cleaning_mets.out[0], ocropy_dewarp.out[0], "OCR-D-OCR")
}
