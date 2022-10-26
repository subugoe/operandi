nextflow.enable.dsl=2

// pipeline parameters
params.venv_path = "\$HOME/venv37-ocrd/bin/activate"
params.file_group = "PRESENTATION"
params.workspace = "$projectDir/ocrd-workspace"
params.mets = "${params.workspace}/mets.xml"
params.reads = "${params.workspace}/${params.file_group}"
params.cleaning = "OFF" // nextflow run <script> --cleaning "ON"/"OFF"
// Nextflow process instance for each OCR-D processor
params.process_instances = 8
params.pages = 265

// log pipeline related information to the console
log.info """\
  O C R - D - W O R K F L O W 2 - Parallel
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

process olena_binarize_sauvola {
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
    ocrd-olena-binarize --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P impl sauvola
    deactivate
    """
}

process anybaseocr_crop {
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

process olena_binarize_kim {
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
    ocrd-olena-binarize --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P impl kim
    deactivate
    """
}

process ocropy_denoise {
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
    ocrd-cis-ocropy-denoise --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P level-of-operation page
    deactivate
    """ 
}

process ocropy_deskew_page {
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
    ocrd-cis-ocropy-deskew --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P level-of-operation page
    deactivate
    """ 
}

process tesserocr_segment_region {
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
    ocrd-tesserocr-segment-region --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num}
    deactivate
    """ 
}

process segment_repair_plausibilized {
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
    ocrd-segment-repair --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P plausibilize true
    deactivate
    """ 
}

process ocropy_deskew_region {
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
    ocrd-cis-ocropy-deskew --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P level-of-operation region
    deactivate
    """ 
}

process ocropy_clip {
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
    ocrd-cis-ocropy-clip --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P level-of-operation region
    deactivate
    """ 
}

process tesserocr_segment_line {
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
    ocrd-tesserocr-segment-line --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num}
    deactivate
    """ 
}

process segment_repair_sanitized {
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
    ocrd-segment-repair --mets ${params.workspace}/mets_${page_num}.xml -I ${input_dir} -O ${output_dir} --page-id PHYS_${page_num} -P sanitize true
    deactivate
    """ 
}

process ocropy_dewarp {
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
    ocrd workspace --mets ${mets_file} merge --force --no-copy-files ${params.workspace}/mets_${page_num}.xml --page-id PHYS_${page_num}
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
    olena_binarize_sauvola(params.file_group, "OCR-D-BIN", dividing_mets.out[1])
    anybaseocr_crop(olena_binarize_sauvola.out[0], "OCR-D-CROP", olena_binarize_sauvola.out[1])
    olena_binarize_kim(anybaseocr_crop.out[0], "OCR-D-BIN2", anybaseocr_crop.out[1])
    ocropy_denoise(olena_binarize_kim.out[0], "OCR-D-BIN-DENOISE",olena_binarize_kim.out[1])
    ocropy_deskew_page(ocropy_denoise.out[0], "OCR-D-BIN-DENOISE-DESKEW", ocropy_denoise.out[1])
    tesserocr_segment_region(ocropy_deskew_page.out[0], "OCR-D-SEG-REG", ocropy_deskew_page.out[1])
    segment_repair_plausibilized(tesserocr_segment_region.out[0], "OCR-D-SEG-REPAIR", tesserocr_segment_region.out[1])
    ocropy_deskew_region(segment_repair_plausibilized.out[0], "OCR-D-SEG-REG-DESKEW", segment_repair_plausibilized.out[1])
    ocropy_clip(ocropy_deskew_region.out[0], "OCR-D-SEG-REG-DESKEW-CLIP", ocropy_deskew_region.out[1])
    tesserocr_segment_line(ocropy_clip.out[0], "OCR-D-SEG-LINE", ocropy_clip.out[1])
    segment_repair_sanitized(tesserocr_segment_line.out[0], "OCR-D-SEG-REPAIR-LINE", tesserocr_segment_line.out[1])
    ocropy_dewarp(segment_repair_sanitized.out[0], "OCR-D-SEG-LINE-RESEG-DEWARP", segment_repair_sanitized.out[1])
    calamari_recognize(ocropy_dewarp.out[0], "OCR-D-OCR", ocropy_dewarp.out[1])

    // Merging mets files representing pages into the main mets file
    // Merged mets files of pages are deleted after merging
    merging_mets(params.mets, calamari_recognize.out[1])
}
