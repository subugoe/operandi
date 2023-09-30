nextflow.enable.dsl=2

// pipeline parameters
params.venv_path = "\$HOME/venv37-ocrd/bin/activate"
params.file_group = "DEFAULT"
params.workspace = "$projectDir/ocrd-workspace"
params.mets = "${params.workspace}/mets.xml"
params.reads = "${params.workspace}/${params.file_group}"
params.cleaning = "OFF" // nextflow run <script> --cleaning "ON"/"OFF"

// log pipeline parameters to the console
log.info """\
  O C R - D - W O R K F L O W 1 - Serial
  ======================================================
  environment       : ${params.venv_path}
  workpace          : ${params.workspace}
  mets              : ${params.mets}
  file_group        : ${params.file_group}
  cleaning          : ${params.cleaning}
  
  OCR-D WORKFLOW REPRESENTED WITH THIS NEXTFLOW SCRIPT:
  ======================================================
  ocrd process \\
  "cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN" \\
  "anybaseocr-crop -I OCR-D-BIN -O OCR-D-CROP" \\
  "skimage-binarize -I OCR-D-CROP -O OCR-D-BIN2 -P method li" \\
  "skimage-denoise -I OCR-D-BIN2 -O OCR-D-BIN-DENOISE -P level-of-operation page" \\
  "tesserocr-deskew -I OCR-D-BIN-DENOISE -O OCR-D-BIN-DENOISE-DESKEW -P operation_level page" \\
  "cis-ocropy-segment -I OCR-D-BIN-DENOISE-DESKEW -O OCR-D-SEG -P level-of-operation page" \\
  "cis-ocropy-dewarp -I OCR-D-SEG -O OCR-D-SEG-LINE-RESEG-DEWARP" \\
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
    ocrd workspace --mets ${mets_file} remove-group --recursive --force THUMBS
    echo "THUMBS fileGrp was removed from the mets file"
    ocrd workspace --mets ${mets_file} remove-group --recursive --force PRESENTATION
    echo "PRESENTATION fileGrp was removed from the mets file"
    deactivate
    """
  else
    """
    echo "Cleaning of unnecessary file groups is turned off"
    """
}

process binarize {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir

  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-binarize --mets ${mets_file} -I ${input_dir} -O ${output_dir}
    deactivate
    """
}

process crop {
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

process skimage_bin {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-skimage-binarize --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P method li
    deactivate
    """
}

process skimage_den {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-skimage-denoise --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P level-of-operation page
    deactivate
    """ 
}

process deskew {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-tesserocr-deskew --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P operation_level page
    deactivate
    """ 
}

process segment {
  input:
    path mets_file
    val input_dir
    val output_dir

  output:
    val output_dir
  
  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-segment --mets ${mets_file} -I ${input_dir} -O ${output_dir} -P level-of-operation page
    deactivate
    """ 
}

process dewarp {
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
    cleaning_mets(params.mets)
    binarize(cleaning_mets.out[0], params.file_group, "OCR-D-BIN")
    crop(cleaning_mets.out[0], binarize.out[0], "OCR-D-CROP")
    skimage_bin(cleaning_mets.out[0], crop.out[0], "OCR-D-BIN2")
    skimage_den(cleaning_mets.out[0], skimage_bin.out[0], "OCR-D-BIN-DENOISE")
    deskew(cleaning_mets.out[0], skimage_den.out[0], "OCR-D-BIN-DENOISE-DESKEW")
    segment(cleaning_mets.out[0], deskew.out[0], "OCR-D-SEG")
    dewarp(cleaning_mets.out[0], segment.out[0], "OCR-D-SEG-LINE-RESEG-DEWARP")
    calamari_recognize(cleaning_mets.out[0], dewarp.out[0], "OCR-D-OCR")
}
