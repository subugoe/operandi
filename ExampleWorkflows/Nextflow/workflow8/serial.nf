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
  O C R - D - T E S T   P I P E L I N E - EXPERIMENTAL
  ===========================================
  environment   : ${params.venv_path}
  workpace      : ${params.workspace}
  mets          : ${params.mets}
  file_group    : ${params.file_group}
  """
  .stripIndent()

process cleaning_mets {
  maxForks 1
  echo true

  input:
    path mets_file

  output:
    path mets_file

  script:
  if (params.cleaning == "ON")
    """
    source "${params.venv_path}"
    echo "Cleaning is turned on"
    ocrd workspace --mets ${mets_file} remove-group --recursive --force THUMBS 
    ocrd workspace --mets ${mets_file} remove-group --recursive --force PRESENTATION 
    deactivate
    """
  else
    """
    echo "Cleaning is turned off"
    """
}

process binarize {
  maxForks 1

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
  maxForks 1

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
  maxForks 1
  
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
  maxForks 1
  
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
  maxForks 1
  
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
  maxForks 1
  
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
  maxForks 1
  
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
  maxForks 1
  
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
    binarize(cleaning_mets.out[0], "DEFAULT", "OCR-D-BIN")
    crop(cleaning_mets.out[0], binarize.out[0], "OCR-D-CROP")
    skimage_bin(cleaning_mets.out[0], crop.out[0], "OCR-D-BIN2")
    skimage_den(cleaning_mets.out[0], skimage_bin.out[0], "OCR-D-BIN-DENOISE")
    deskew(cleaning_mets.out[0], skimage_den.out[0], "OCR-D-BIN-DENOISE-DESKEW")
    segment(cleaning_mets.out[0], deskew.out[0], "OCR-D-SEG")
    dewarp(cleaning_mets.out[0], segment.out[0], "OCR-D-SEG-LINE-RESEG-DEWARP")
    calamari_recognize(cleaning_mets.out[0], dewarp.out[0], "OCR-D-OCR")
}
