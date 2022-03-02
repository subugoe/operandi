// enables a syntax extension that allows definition of module libraries
nextflow.enable.dsl=2

// pipeline parameters
params.venv = "\$HOME/venv37-ocrd/bin/activate"
params.workspace = "$projectDir/ocrd-workspace/"
params.mets = "$projectDir/ocrd-workspace/mets.xml"
params.reads = "$projectDir/ocrd-workspace/OCR-D-IMG" // The first input directory
params.outs = "$projectDir/ocrd-workspace/OCR-D-BIN"

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
         outs          : ${params.outs}
         """
         .stripIndent()

// Not used here, just for reference
process all_in_one {
  maxForks 1 // force to run sequentially
  echo true
  //publishDir --> directive which publishes the obtained results in another directory

  input:
    path mets_file 
    path dir_name

  script:
  """ 
  echo "Directory: ${dir_name}"
  
  source "${params.venv}"
  ocrd-cis-ocropy-binarize -I "OCR-D-IMG" -O "OCR-D-BIN"
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
// Not used here, just for reference

process ocropy_binarize {
  maxForks 1
	
  input:
    path mets_file
    val input_dir
    val output_dir
	
  output:
    val output_dir
	
  script:
  """	
  source "${params.venv}"
  ocrd-cis-ocropy-binarize -I ${input_dir} -O ${output_dir}
  deactivate
  """
}

process anybaseocr_crop {
  maxForks 1
	
  input:
    path mets_file
    val input_dir
    val output_dir
	
  output:
    val output_dir
	
  script:
  """
  source "${params.venv}"
  ocrd-anybaseocr-crop -I ${input_dir} -O ${output_dir}
  deactivate
  """
}

process skimage_binarize {
  maxForks 1
	
  input:
    path mets_file
    val input_dir
    val output_dir
	
  output:
    val output_dir
	
  script:
  """
  source "${params.venv}"
  ocrd-skimage-binarize -I ${input_dir} -O ${output_dir} -P method li
  deactivate
  """
}

process skimage_denoise {
  maxForks 1
	
  input:
    path mets_file
    val input_dir
    val output_dir
	
  output:
    val output_dir
	
  script:
  """
  source "${params.venv}"
  ocrd-skimage-denoise -I ${input_dir} -O ${output_dir} -P level-of-operation page
  deactivate
  """	
}

process tesserocr_deskew {
  maxForks 1
	
  input:
    path mets_file
    val input_dir
    val output_dir
	
  output:
    val output_dir
	
  script:
  """
  source "${params.venv}"
  ocrd-tesserocr-deskew -I ${input_dir} -O ${output_dir} -P operation_level page
  deactivate
  """	
}

process cis_ocropy_segment {
  maxForks 1
	
  input:
    path mets_file
    val input_dir
    val output_dir
	
  output:
    val output_dir
	
  script:
  """
  source "${params.venv}"
  ocrd-cis-ocropy-segment -I ${input_dir} -O ${output_dir} -P level-of-operation page
  deactivate
  """	
}

process cis_ocropy_dewarp {
  maxForks 1
	
  input:
    path mets_file
    val input_dir
    val output_dir
	
  output:
    val output_dir
	
  script:
  """
  source "${params.venv}"
  ocrd-cis-ocropy-dewarp -I ${input_dir} -O ${output_dir}
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
  source "${params.venv}"
  ocrd-calamari-recognize  -I ${input_dir} -O ${output_dir} -P checkpoint_dir qurator-gt4histocr-1.0
  deactivate
  """
}

// This is the main workflow
workflow {

  main:
    // input_dir_ch = Channel.fromPath(params.reads, type: 'dir')
    ocropy_binarize(params.mets, "OCR-D-IMG", "OCR-D-BIN")
    anybaseocr_crop(params.mets, ocropy_binarize.out, "OCR-D-CROP")
    skimage_binarize(params.mets, anybaseocr_crop.out, "OCR-D-BIN2")
    skimage_denoise(params.mets, skimage_binarize.out, "OCR-D-BIN-DENOISE")
    tesserocr_deskew(params.mets, skimage_denoise.out, "OCR-D-BIN-DENOISE-DESKEW")
    cis_ocropy_segment(params.mets, tesserocr_deskew.out, "OCR-D-SEG")
    cis_ocropy_dewarp(params.mets, cis_ocropy_segment.out, "OCR-D-SEG-LINE-RESEG-DEWARP")
    calamari_recognize(params.mets, cis_ocropy_dewarp.out, "OCR-D-OC")

}














