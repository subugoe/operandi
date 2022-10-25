nextflow.enable.dsl=2

// pipeline parameters
params.venv_path = "\$HOME/venv37-ocrd/bin/activate"
params.file_group = "DEFAULT"
params.workspace = "$projectDir/ocrd-workspace"
params.mets = "${params.workspace}/mets.xml"
params.reads = "${params.workspace}/${params.file_group}"
params.cleaning = "OFF" // nextflow run <script> --cleaning "ON"/"OFF"
// Nextflow process instance for each OCR-D processor
params.process_instances = 8
params.pages = 29

// log pipeline related information to the console
log.info """\
  O C R - D - W O R K F L O W 1 - Parallel
  ======================================================
  environment       : ${params.venv_path}
  workpace          : ${params.workspace}
  mets              : ${params.mets}
  file_group        : ${params.file_group}
  pages             : ${params.pages}
  process_instances : ${params.process_instances}
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
  // Must be a single instance - modifying the main mets file
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

process dividing_mets {
  maxForks params.process_instances

  input:
    path mets_file
    val page_integer

  output:
    val "mets_\${page_num}.xml"
    env page_num

  // page_integer -> page_num
  // 1 -> 0001, 10 -> 0010
  script:
    """
    page_num=\$(printf "%04d" ${page_integer})
    cp ${mets_file} ${params.workspace}/mets_\${page_num}.xml
    """
}

process binarize {
  maxForks params.process_instances

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
  maxForks params.process_instances

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
  maxForks params.process_instances
  
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
  maxForks params.process_instances
  
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
  maxForks params.process_instances
  
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
  maxForks params.process_instances
  
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
  maxForks params.process_instances
  
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
  maxForks params.process_instances
  
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
  // Must be a single instance - modifying the main mets file
  maxForks 1
  
  input:
    path mets_file
    val page_num

  output:
    val page_num

  script:
    """
    source "${params.venv_path}"
    ocrd workspace --mets ${mets_file} merge --force --no-copy-files ${params.workspace}/mets_${page_num}.xml
    rm ${params.workspace}/mets_${page_num}.xml
    deactivate
    """
}

// This is the main workflow
workflow {

  main:
    // The input channel that holds list of integers for pages
    ch_page = Channel.of(1..params.pages)

    // Cleaning the mets if turned on
    cleaning_mets(params.mets)

    // Duplicating the mets file as many times as pages are in the workspace
    // Each mets file is then labeled according to the page it represents
    dividing_mets(cleaning_mets.out[0], ch_page)

    // OCR-D workflow processes
    // NOTE: The binarization processor also downloads the locally missing files
    // We can do this in parallel, unlike with the download_workspace process
    binarize(params.file_group, "OCR-D-BIN", dividing_mets.out[1])
    crop(binarize.out[0], "OCR-D-CROP", binarize.out[1])
    skimage_bin(crop.out[0], "OCR-D-BIN2", crop.out[1])
    skimage_den(skimage_bin.out[0], "OCR-D-BIN-DENOISE", skimage_bin.out[1])
    deskew(skimage_den.out[0], "OCR-D-BIN-DENOISE-DESKEW", skimage_den.out[1])
    segment(deskew.out[0], "OCR-D-SEG", deskew.out[1])
    dewarp(segment.out[0], "OCR-D-SEG-LINE-RESEG-DEWARP", segment.out[1])
    calamari_recognize(dewarp.out[0], "OCR-D-OCR", dewarp.out[1])

    // Merging mets files representing pages into the main mets file
    // Merged mets files of pages are deleted after merging
    merging_mets(params.mets, calamari_recognize.out[1])
}
