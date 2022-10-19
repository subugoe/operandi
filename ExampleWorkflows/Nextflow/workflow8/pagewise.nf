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

process dividing_mets {
  maxForks 8

  input:
    path mets_file
    val page_num

  output:
    val "mets_${page_num}.xml"
    val page_num

  script:
    """
    source "${params.venv_path}"
    cp mets.xml ${params.workspace}/mets_${page_num}.xml
    deactivate
    """
}

process binarize {
  maxForks 8

  input:
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num

  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-binarize --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num}
    deactivate
    """
}

process crop {
  maxForks 8

  input:
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num

  script:
    """
    source "${params.venv_path}"
    ocrd-anybaseocr-crop --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num}
    deactivate
    """
}

process skimage_bin {
  maxForks 8
  
  input:
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num
  
  script:
    """
    source "${params.venv_path}"
    ocrd-skimage-binarize --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P method li
    deactivate
    """
}

process skimage_den {
  maxForks 8
  
  input:
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num
  
  script:
    """
    source "${params.venv_path}"
    ocrd-skimage-denoise --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P level-of-operation page
    deactivate
    """ 
}

process deskew {
  maxForks 8
  
  input:
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num
  
  script:
    """
    source "${params.venv_path}"
    ocrd-tesserocr-deskew --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P operation_level page
    deactivate
    """ 
}

process segment {
  maxForks 8
  
  input:
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num
  
  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-segment --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P level-of-operation page
    deactivate
    """ 
}

process dewarp {
  maxForks 8
  
  input:
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num
  
  script:
    """
    source "${params.venv_path}"
    ocrd-cis-ocropy-dewarp --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num}
    deactivate
    """   
}

process calamari_recognize {
  maxForks 8
  
  input:
    val input_dir
    val output_dir
    val page_num

  output:
    val output_dir
    val page_num

  script:
    """
    source "${params.venv_path}"
    ocrd-calamari-recognize --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P checkpoint_dir qurator-gt4histocr-1.0
    deactivate
    """
}

process merging_mets {
  maxForks 1
  
  input:
    path mets_file
    val page_num

  output:
    val page_num

  script:
    """
    source "${params.venv_path}"
    ocrd workspace --mets ${mets_file} merge --overwrite --no-copy-files ${params.workspace}/mets_${page_num}.xml
    rm ${params.workspace}/mets_${page_num}.xml
    deactivate
    """
}

// This is the main workflow
workflow {

  main:
    // This line cannot be executed in parallel
    // download_workspace(params.mets, params.file_group)

    // A way to read all files from a directory
    // input_dir_ch_bin = Channel.fromPath(params.reads, type: 'dir')

    // Unfortunately there isn't a shorter way to implement this
    ch_page = Channel.of("0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009", "0010",
                         "0011", "0012", "0013", "0014", "0015", "0016", "0017", "0018", "0019", "0020",
                         "0021", "0022", "0023", "0024", "0025", "0026", "0027", "0028", "0029")
    cleaning_mets(params.mets)
    dividing_mets(cleaning_mets.out[0], ch_page)
    binarize("DEFAULT", "OCR-D-BIN", dividing_mets.out[1])
    crop(binarize.out[0], "OCR-D-CROP", binarize.out[1])
    skimage_bin(crop.out[0], "OCR-D-BIN2", crop.out[1])
    skimage_den(skimage_bin.out[0], "OCR-D-BIN-DENOISE", skimage_bin.out[1])
    deskew(skimage_den.out[0], "OCR-D-BIN-DENOISE-DESKEW", skimage_den.out[1])
    segment(deskew.out[0], "OCR-D-SEG", deskew.out[1])
    dewarp(segment.out[0], "OCR-D-SEG-LINE-RESEG-DEWARP", segment.out[1])
    calamari_recognize(dewarp.out[0], "OCR-D-OCR", dewarp.out[1])
    merging_mets(params.mets, calamari_recognize.out[1])
}
