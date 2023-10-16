// enables a syntax extension that allows definition of module libraries
nextflow.enable.dsl=2

// pipeline parameters 
params.indir = "$projectDir/input/"
params.outdir = "$projectDir/output/"
params.reads = "$projectDir/input/data*"
params.venv = "\$HOME/venv-ocrd/bin/activate"

// log pipeline parameters to the console
log.info """\
         O P E R A N D I - T E S T   P I P E L I N E 3
         ===========================================
         indir      : ${params.indir}
         outdir     : ${params.outdir}
         reads      : ${params.reads}
         venv       : ${params.venv}
         """
         .stripIndent()

// each folder gets its own processor to process the data
process ocrd_processor {
   echo true
   publishDir params.outdir

   input:
   path dir_name // from input_dir_ch
   
   output:
   path "${dir_name}/data/OCR-D-SEG-BLOCK"
   
   script:
   """ 
   echo "Directory: ${dir_name}"
   echo "Output Dir: ${params.outdir}${dir_name}"
   
   cd "${dir_name}/data"
   
   source "${params.venv}"
   ocrd-vandalize -I "OCR-D-IMG" -O "OCR-D-SEG-BLOCK" --overwrite
   deactivate
   
   """
}

// This is the main workflow
workflow {

   main:
      // all directories that match the params.reads pattern are loaded to the channel
      input_dir_ch = Channel.fromPath(params.reads, type: 'dir')
      ocrd_processor(input_dir_ch)

}














