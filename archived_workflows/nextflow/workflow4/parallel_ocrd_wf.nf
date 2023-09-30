// enables a syntax extension that allows definition of module libraries
nextflow.enable.dsl=2

// pipeline parameters
params.venv = "\$HOME/venv37-ocrd/bin/activate"
params.workspace = "$projectDir/ocrd-workspace/sub-workspace-*"
params.mets = "$projectDir/ocrd-workspace/**/mets.xml"

// nextflow run <my script> --foo Hello
// Then, the parameter is accessed with: params.foo

// log pipeline parameters to the console
log.info """\
         O P E R A N D I - T E S T   P I P E L I N E 4 - EXPERIMENTAL
         ===========================================
         venv          : ${params.venv}
         ocrd-workpace : ${params.workspace}
         mets          : ${params.mets}
         """
         .stripIndent()

process ocropy_binarize {
  maxForks 4
	
  input:
    path mets_file
    path workspace
    val input_dir
    val output_dir
	
  output:
    path mets_file
    path workspace
    val output_dir

  script:
  """	
  source "${params.venv}"
  ocrd-cis-ocropy-binarize -I ${input_dir} -O ${output_dir}
  deactivate
  """
}

process anybaseocr_crop {
  maxForks 4
	
  input:
    path mets_file
    path workspace
    val input_dir
    val output_dir
	
  output:
    path mets_file
    path workspace
    val output_dir
	
  script:
  """
  source "${params.venv}"
  ocrd-anybaseocr-crop -I ${input_dir} -O ${output_dir}
  deactivate
  """
}

process skimage_binarize {
  maxForks 4
	
  input:
    path mets_file
    path workspace
    val input_dir
    val output_dir
	
  output:
    path mets_file
    path workspace
    val output_dir
	
  script:
  """
  source "${params.venv}"
  ocrd-skimage-binarize -I ${input_dir} -O ${output_dir} -P method li
  deactivate
  """
}

process skimage_denoise {
  maxForks 4
	
  input:
    path mets_file
    path workspace
    val input_dir
    val output_dir
	
  output:
    path mets_file
    path workspace
    val output_dir
	
  script:
  """
  source "${params.venv}"
  ocrd-skimage-denoise -I ${input_dir} -O ${output_dir} -P level-of-operation page
  deactivate
  """	
}

process tesserocr_deskew {
  maxForks 4
	
  input:
    path mets_file
    path workspace
    val input_dir
    val output_dir
	
  output:
    path mets_file
    path workspace
    val output_dir
	
  script:
  """
  source "${params.venv}"
  ocrd-tesserocr-deskew -I ${input_dir} -O ${output_dir} -P operation_level page
  deactivate
  """	
}

process cis_ocropy_segment {
  // setting this processor to 4 forks, causes fileGrp not found errors
  // this one runs sequentially
  maxForks 1
	
  input:
    path mets_file
    path workspace
    val input_dir
    val output_dir
	
  output:
    path mets_file
    path workspace
    val output_dir
	
  script:
  """
  source "${params.venv}"
  ocrd-cis-ocropy-segment -I ${input_dir} -O ${output_dir} -P level-of-operation page
  deactivate
  """	
}

process cis_ocropy_dewarp {
  maxForks 4
	
  input:
    path mets_file
    path workspace
    val input_dir
    val output_dir
	
  output:
    path mets_file
    path workspace
    val output_dir
	
  script:
  """
  source "${params.venv}"
  ocrd-cis-ocropy-dewarp -I ${input_dir} -O ${output_dir}
  deactivate
  """		
}

process calamari_recognize {
  maxForks 4
	
  input:
    path mets_file
    path workspace
    val input_dir
    val output_dir
	
  output:
    path mets_file
    path workspace
    val output_dir

  script:
  """
  source "${params.venv}"
  ocrd-calamari-recognize  -I ${input_dir} -O ${output_dir} -P checkpoint_dir qurator-gt4histocr-1.0
  deactivate
  """
}

process print_input {
  input:
    val mets_file
    val workspace
  
  exec:
    println "Workspace: ${workspace} Mets: ${mets_file} DirName: ${dir_name}"
}

workflow flow_of_processors {

  take: 
    input_mets_ch
    input_workspace_ch

  main:
    ocr_d_img = Channel.value("OCR-D-IMG")
    ocr_d_bin = Channel.value("OCR-D-BIN")
    ocr_d_crop = Channel.value("OCR-D-CROP")
    ocr_d_bin2 = Channel.value("OCR-D-BIN2")
    ocr_d_denoise = Channel.value("OCR-D-BIN-DENOISE")
    ocr_d_deskew = Channel.value("OCR-D-BIN-DENOISE-DESKEW")
    ocr_d_seg = Channel.value("OCR-D-SEG")
    ocr_d_dewarp = Channel.value("OCR-D-SEG-LINE-RESEG-DEWARP")
    ocr_d_oc = Channel.value("OCR-D-OC")

    // print_input(input_mets_ch, input_workspace_ch)
    ocropy_binarize(input_mets_ch, input_workspace_ch, ocr_d_img, ocr_d_bin)
    anybaseocr_crop(ocropy_binarize.out[0], ocropy_binarize.out[1], ocropy_binarize.out[2], ocr_d_crop)
    skimage_binarize(anybaseocr_crop.out[0], anybaseocr_crop.out[1], anybaseocr_crop.out[2], ocr_d_bin2)
    skimage_denoise(skimage_binarize.out[0], skimage_binarize.out[1], skimage_binarize.out[2], ocr_d_denoise)
    tesserocr_deskew(skimage_denoise.out[0], skimage_denoise.out[1], skimage_denoise.out[2], ocr_d_deskew)
    cis_ocropy_segment(tesserocr_deskew.out[0], tesserocr_deskew.out[1], tesserocr_deskew.out[2], ocr_d_seg)
    cis_ocropy_dewarp(cis_ocropy_segment.out[0], cis_ocropy_segment.out[1], cis_ocropy_segment.out[2], ocr_d_dewarp)
    calamari_recognize(cis_ocropy_dewarp.out[0], cis_ocropy_dewarp.out[1], cis_ocropy_dewarp.out[2], ocr_d_oc)

}

// This is the main workflow
workflow {

  main:
    input_workspace_ch = Channel.fromPath(params.workspace, type: 'dir')
    input_mets_ch = Channel.fromPath(params.mets, type: 'any')

    flow_of_processors(input_mets_ch, input_workspace_ch)
   
}
