// enables a syntax extension that allows definition of module libraries
nextflow.enable.dsl=2

// pipeline parameters
params.workspace = "$projectDir/ocrd-workspace/"
params.mets = "$projectDir/ocrd-workspace/mets.xml"
params.reads = "$projectDir/ocrd-workspace/OCR-D-IMG"
params.tempdir = "null"

// nextflow run <my script> --tempdir TEMPDIR
// Then, the parameter is accessed with: params.tempdir

// log pipeline parameters to the console
log.info """\
         O P E R A N D I - T E S T   P I P E L I N E 5
         ===========================================
         ocrd-workpace : ${params.workspace}
         tempdir       : ${params.tempdir}
         mets          : ${params.mets}
         reads         : ${params.reads}
         """
         .stripIndent()

process ocrd_cis_ocropy_binarize {

  maxForks 1 // force to run sequentially
  echo true

  input:
    path mets_file 
    path dir_name
  
  script:
  """
  pwd
  ls -la
  singularity exec --bind ${params.tempdir} docker://ocrd/all:maximum ocrd-cis-ocropy-binarize -m ${mets_file} -I ${dir_name} -O "OCR-D-BIN"
  """
}

// This is the main workflow
workflow {

  main:
    input_dir_ch = Channel.fromPath(params.reads, type: 'dir')
    ocrd_cis_ocropy_binarize(params.mets, input_dir_ch)
    
}














