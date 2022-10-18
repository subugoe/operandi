nextflow.enable.dsl=2

// pipeline parameters
params.venv_path = "\$HOME/venv37-ocrd/bin/activate"
params.file_group = "DEFAULT"
params.workspace = "$projectDir/ocrd-workspace"
params.mets = "${params.workspace}/mets.xml"
params.reads = "${params.workspace}/${params.file_group}"

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

process binarize {
  maxForks 1

  input:
    path mets_file
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num

  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-binarize --mets ${mets_file} -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num}
    deactivate
    """
}

process crop {
  maxForks 1

  input:
    path mets_file
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num

  script:
    """
    source "${params.venv_path}"
    ocrd-anybaseocr-crop --mets ${mets_file} -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num}
    deactivate
    """
}

process skimage_bin {
  maxForks 1
  
  input:
    path mets_file
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num
  
  script:
    """
    source "${params.venv_path}"
    ocrd-skimage-binarize --mets ${mets_file} -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P method li
    deactivate
    """
}

process skimage_den {
  maxForks 1
  
  input:
    path mets_file
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num
  
  script:
    """
    source "${params.venv_path}"
    ocrd-skimage-denoise --mets ${mets_file} -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P level-of-operation page
    deactivate
    """ 
}

process deskew {
  maxForks 1
  
  input:
    path mets_file
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num
  
  script:
    """
    source "${params.venv_path}"
    ocrd-tesserocr-deskew --mets ${mets_file} -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P operation_level page
    deactivate
    """ 
}

process segment {
  // setting this processor to more forks, 
  // causes fileGrp not found errors
  // this one runs sequentially
  maxForks 1
  
  input:
    path mets_file
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num
  
  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-segment --mets ${mets_file} -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P level-of-operation page
    deactivate
    """ 
}

process dewarp {
  maxForks 1
  
  input:
    path mets_file
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num
  
  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-dewarp --mets ${mets_file} -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num}
    deactivate
    """   
}

process calamari_recognize {
  maxForks 1
  
  input:
    path mets_file
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num

  script:
    """
    source "${params.venv_path}"
    ocrd-calamari-recognize --mets ${mets_file} -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P checkpoint_dir qurator-gt4histocr-1.0
    deactivate
    """
}

// This is the main workflow
workflow {

  main:
    // Unfortunately there isn't a shorter way to implement this
    ch_page = Channel.of("0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009", "0010",
                         "0011", "0012", "0013", "0014", "0015", "0016", "0017", "0018", "0019", "0020",
                         "0021", "0022", "0023", "0024", "0025", "0026", "0027", "0028", "0029")
    binarize(params.mets, "DEFAULT", "OCR-D-BIN", ch_page)
    crop(params.mets, binarize.out[0], "OCR-D-CROP", binarize.out[1])
    skimage_bin(params.mets, crop.out[0], "OCR-D-BIN2", crop.out[1])
    skimage_den(params.mets, skimage_bin.out[0], "OCR-D-BIN-DENOISE", skimage_bin.out[1])
    deskew(params.mets, skimage_den.out[0], "OCR-D-BIN-DENOISE-DESKEW", skimage_den.out[1])
    segment(params.mets, deskew.out[0], "OCR-D-SEG", deskew.out[1])
    dewarp(params.mets, segment.out[0], "OCR-D-SEG-LINE-RESEG-DEWARP", segment.out[1])
    calamari_recognize(params.mets, dewarp.out[0], "OCR-D-OCR", dewarp.out[1])
}
