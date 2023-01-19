// enables a syntax extension that allows definition of module libraries
nextflow.enable.dsl=2

// pipeline parameters
params.workspace = "$projectDir/ocrd-workspace/"
params.mets = "$projectDir/ocrd-workspace/mets.xml"
params.file_group = "DEFAULT"
params.reads = "$projectDir/ocrd-workspace/DEFAULT"
params.volume_dir = "null"
params.olahd_endpoint = ""
params.olahd_username = ""
params.olahd_password = ""

// nextflow run <my script> --volume_dir TEMPDIR
// Then, the parameter is accessed with: params.tempdir

// log pipeline parameters to the console
log.info """\
  O P E R A N D I - L O C A L - T E S T   P I P E L I N E
  ===========================================
  workpace      : ${params.workspace}
  mets          : ${params.mets}
  file_group    : ${params.file_group}
  volume_dir    : ${params.volume_dir}
  olahd_username: ${params.olahd_username}
  """
  .stripIndent()

process download_workspace {
  publishDir params.reads
  // limit instances to 1
  // (force to run sequentially)
  maxForks 1
  echo true

  input:
    path mets_file
    val file_group

  script:
  """
  docker run --rm -v ${params.volume_dir}:/data -w /data -- ocrd/all:maximum ocrd workspace find --file-grp ${file_group} --download --wait 1
  """
}

process ocrd_cis_ocropy_binarize {
  // limit instances to 1
  // (force to run sequentially)
  maxForks 1
  echo true

  input:
    path mets_file
    path dir_name
  output:
    path dir_name

  script:
  """
  docker run --rm -v ${params.volume_dir}:/data -w /data -- ocrd/all:maximum ocrd-cis-ocropy-binarize -m ${mets_file} -I ${dir_name} -O "OCR-D-BIN"
  """
}

process save_to_olahd {
  // limit instances to 1
  // (force to run sequentially)
  maxForks 1
  echo true

  input:
    path mets_file
    // variable only needed to cause waiting for the completition of other processors
    path dir_name
    val olahd_endpoint
    val olahd_username
    val olahd_password

  script:
  """
  docker run --rm -v ${params.volume_dir}:/data -w /data -- ocrd/all:maximum ocrd-olahd-client -m ${mets_file} -p '{"endpoint": "${olahd_endpoint}", "username": "${olahd_username}", "password": "${olahd_password}"}'
  """
}

// This is the main workflow
workflow {

  main:
    download_workspace(params.mets, params.file_group)
    input_dir_ch = Channel.fromPath(params.reads, type: 'dir')
    ocrd_cis_ocropy_binarize(params.mets, input_dir_ch)
    if (params.olahd_username)
        save_to_olahd(params.mets, ocrd_cis_ocropy_binarize.out, params.olahd_endpoint, params.olahd_username, params.olahd_password)
}
