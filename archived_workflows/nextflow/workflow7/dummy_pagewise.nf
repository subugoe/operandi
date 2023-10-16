nextflow.enable.dsl=2

// pipeline parameters
params.venv_path = "\$HOME/venv37-ocrd/bin/activate"
params.workspace = "$projectDir/ocrd-workspace/"
params.mets = "$projectDir/ocrd-workspace/mets.xml"
params.file_group = "DEFAULT"

// log pipeline parameters to the console
log.info """\
  O P E R A N D I - T E S T   P I P E L I N E 8 - EXPERIMENTAL
  ===========================================
  environment   : ${params.venv_path}
  workpace      : ${params.workspace}
  mets          : ${params.mets}
  file_group    : ${params.file_group}
  """
  .stripIndent()

// Not used, shown for reference
process download_workspace {
  publishDir params.reads
  maxForks 1

  input:
    path mets_file
    val file_group

  script:
  """
  source "${params.venv_path}"
  ocrd workspace find --file-grp ${file_group} --download --wait 1
  deactivate
  """
}

process dummy_pagewise_binarize {
  publishDir "$projectDir/ocrd-workspace/OCR-D-BIN"
  maxForks 4

  input:
    val page_number

  output:
    file "bin_${page_number}"
  
  script:
  """
  source "${params.venv_path}"
  echo ${page_number} > bin_${page_number}
  sleep 2
  deactivate
  """
}

process dummy_pagewise_crop {
  publishDir "$projectDir/ocrd-workspace/OCR-D-CROP"
  maxForks 4

  input:
    file page_number_file

  output:
    file "crop_${page_number_file}"

  script:
    """
    source "${params.venv_path}"
    cat ${page_number_file} > crop_${page_number_file}
    deactivate
    """
}

// This is the main workflow
workflow {

  main:
    // This line cannot be executed in parallel
    // download_workspace(params.mets, params.file_group)

    // A way to read all files from a directory
    // input_dir_ch_bin = Channel.fromPath("$projectDir/ocrd-workspace/DEFAULT/*", type: 'file')

    // Files from the above channel would be passed in a real scenario
    // For the dummy implementation just numbers representing pages between 1 and 29 are used
    ch_page = Channel.of(1..32)
    dummy_pagewise_binarize(ch_page)
    dummy_pagewise_crop(dummy_pagewise_binarize.out)
}
