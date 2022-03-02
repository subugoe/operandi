// enables a syntax extension that allows definition of module libraries
nextflow.enable.dsl=2

// pipeline parameters
params.venv = "\$HOME/venv37-ocrd/bin/activate"
params.workspace = "$projectDir/ocrd-workspace/"
params.mets = "$projectDir/ocrd-workspace/mets.xml"
params.reads = "$projectDir/ocrd-workspace/OCR-D-IMG"

// nextflow run <my script> --foo Hello
// Then, the parameter is accessed with: params.foo

// log pipeline parameters to the console
log.info """\
         O P E R A N D I - T E S T   P I P E L I N E 4
         ===========================================
         venv          : ${params.venv}
         ocrd-workpace : ${params.workspace}
         mets          : ${params.mets}
         reads         : ${params.reads}
         """
         .stripIndent()

process all_in_one {
  maxForks 1 // force to run sequentially
  echo true
  // publishDir --> directive which publishes the obtained results in another directory

  input:
    path mets_file 
    path dir_name
   
  script:
  """    
  echo "Directory: ${dir_name}"
  
  source "${params.venv}"
  ocrd-cis-ocropy-binarize -I ${dir_name} -O "OCR-D-BIN"
  ocrd-anybaseocr-crop -I "OCR-D-BIN" -O "OCR-D-CROP"
  ocrd-skimage-binarize -I "OCR-D-CROP" -O "OCR-D-BIN2" -P method li
  ocrd-skimage-denoise -I "OCR-D-BIN2" -O "OCR-D-BIN-DENOISE" -P level-of-operation page
  ocrd-tesserocr-deskew -I "OCR-D-BIN-DENOISE" -O "OCR-D-BIN-DENOISE-DESKEW" -P operation_level page
  ocrd-cis-ocropy-segment -I "OCR-D-BIN-DENOISE-DESKEW" -O "OCR-D-SEG" -P level-of-operation page
  ocrd-cis-ocropy-dewarp -I "OCR-D-SEG" -O "OCR-D-SEG-LINE-RESEG-DEWARP"
  ocrd-calamari-recognize -I "OCR-D-SEG-LINE-RESEG-DEWARP" -O "OCR-D-OC" -P checkpoint_dir qurator-gt4histocr-1.0

  deactivate
  """
  
}

// This is the main workflow
workflow {

  main:
    input_dir_ch = Channel.fromPath(params.reads, type: 'dir')
    all_in_one(params.mets, input_dir_ch)
    
}














