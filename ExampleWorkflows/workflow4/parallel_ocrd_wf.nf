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
         O P E R A N D I - T E S T   P I P E L I N E 4
         ===========================================
         venv          : ${params.venv}
         ocrd-workpace : ${params.workspace}
         mets          : ${params.mets}
         """
         .stripIndent()


// Conditional scripts example
bin_method = 'skimage'
process binarization_step {
  maxForks 4
	
  input:
    path mets_file
    path workspace
    val input_dir
    val output_dir
	
  output:
    val output_dir
	
  script:
    if (bin_method == 'skimage')
      """	
      echo "skimage"
      source "${params.venv}"
      ocrd-skimage-binarize -I ${input_dir} -O ${output_dir}
      deactivate
      """
    else if (bin_method == 'cis-ocropy')
      """
      echo "cis-ocropy"
      source "${params.venv}"
      ocrd-cis-ocropy-binarize -I ${input_dir} -O ${output_dir}
      deactivate
      """
    else {
      """
      echo "NO-MATCH!"
      """
	}
}
// Conditional scripts example


process all_in_one {
  maxForks 4 // Maximum 4 forks in parallel possible
  echo true
  //publishDir params.workspace

  input:
    path current_mets
    path current_workspace
  
  // script block
  script:
  """ 
  echo "Workspace: ${current_workspace}"
  echo "Mets: ${current_mets}"
  
  source "${params.venv}"
  ocrd-cis-ocropy-binarize -I "OCR-D-IMG" -O "OCR-D-BIN"
  ocrd-anybaseocr-crop -I "OCR-D-BIN" -O "OCR-D-CROP"
  ocrd-skimage-binarize -I "OCR-D-CROP" -O "OCR-D-BIN2" -P method li
  ocrd-skimage-denoise -I "OCR-D-BIN2" -O "OCR-D-BIN-DENOISE" -P level-of-operation page
  ocrd-tesserocr-deskew -I "OCR-D-BIN-DENOISE" -O "OCR-D-BIN-DENOISE-DESKEW" -P operation_level page
  // Segmentation parallelization works fine here
  ocrd-cis-ocropy-segment -I "OCR-D-BIN-DENOISE-DESKEW" -O "OCR-D-SEG" -P level-of-operation page
  ocrd-cis-ocropy-dewarp -I "OCR-D-SEG" -O "OCR-D-SEG-LINE-RESEG-DEWARP"
  ocrd-calamari-recognize -I "OCR-D-SEG-LINE-RESEG-DEWARP" -O "OCR-D-OC" -P checkpoint_dir qurator-gt4histocr-1.0

  deactivate
  """
}

// Called inside flow_of_processors
process ocropy_binarize {
  maxForks 4
	
  input:
    path mets_file
    path workspace
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
  maxForks 4
	
  input:
    path mets_file
    path workspace
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
  maxForks 4
	
  input:
    path mets_file
    path workspace
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
  maxForks 4
	
  input:
    path mets_file
    path workspace
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
  maxForks 4
	
  input:
    path mets_file
    path workspace
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
  // setting this processor to 4 forks, causes fileGrp not found errors
  // this one runs sequentially
  maxForks 1
	
  input:
    path mets_file
    path workspace
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
  maxForks 4
	
  input:
    path mets_file
    path workspace
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
  maxForks 4
	
  input:
    path mets_file
    path workspace
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

process print_input {
  input:
    val mets_file
    val workspace
  
  // Executable block, loops and anything else fancy that the Groovy offers can be used inside
  exec:
    // Groovy programming language
    println "Workspace: ${workspace} Mets: ${mets_file}"
}

// Called inside flow_of_processors

workflow flow_of_processors {

  take: 
    input_mets_ch
    input_workspace_ch

  main:
    // all processes run in a non-blocking way
    print_input(input_mets_ch, input_workspace_ch)
    ocropy_binarize(input_mets_ch, input_workspace_ch, "OCR-D-IMG", "OCR-D-BIN")
    anybaseocr_crop(input_mets_ch, input_workspace_ch, ocropy_binarize.out, "OCR-D-CROP")
    skimage_binarize(input_mets_ch, input_workspace_ch, anybaseocr_crop.out, "OCR-D-BIN2")
    skimage_denoise(input_mets_ch, input_workspace_ch, skimage_binarize.out, "OCR-D-BIN-DENOISE")
    tesserocr_deskew(input_mets_ch, input_workspace_ch, skimage_denoise.out, "OCR-D-BIN-DENOISE-DESKEW")
    cis_ocropy_segment(input_mets_ch, input_workspace_ch, tesserocr_deskew.out, "OCR-D-SEG")
    cis_ocropy_dewarp(input_mets_ch, input_workspace_ch, cis_ocropy_segment.out, "OCR-D-SEG-LINE-RESEG-DEWARP")
    calamari_recognize(input_mets_ch, input_workspace_ch, cis_ocropy_dewarp.out, "OCR-D-OC")
   
  // It is possible to pass output results from sub-workflows as well, e.g.:
  //emit:
    //calamari_recognize.out // returns "OCR-D-OC"
}

// This is the main workflow
workflow {

  main:
    input_workspace_ch = Channel.fromPath(params.workspace, type: 'dir')
    input_mets_ch = Channel.fromPath(params.mets, type: 'any')

    // this sub-workflow is executed 4 times in parallel because we receive 4 workspaces and 4 mets from the channels
    // cis_ocropy_segment runs sequentially! Otherwise it produces errors.
    flow_of_processors(input_mets_ch, input_workspace_ch)

    // this process is executed 4 times in parallel
    // gives faster processing time than the flow_of_processors due to the 
    // error that cis_ocropy_segment produces when run in parallel 4 times
    // all_in_one(input_mets_ch, input_workspace_ch)
        

    // Conditional scripts example
    // put in comments the two lines above and execute only the line below
    // binarization_step(input_mets_ch, input_workspace_ch, "OCR-D-IMG", "OCR-D-BIN")        
}
