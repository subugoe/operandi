// enables a syntax extension that allows definition of module libraries
nextflow.enable.dsl=2

// pipeline parameters
params.input_folder = "$projectDir/input_folder"
params.step1_out    = "$projectDir/step1_out"
params.step2_out    = "$projectDir/step2_out"
params.step3_out    = "$projectDir/step3_out"

// log pipeline parameters to the console
log.info """\
         O P E R A N D I - T E S T   P I P E L I N E 6 - PIPELINED PARALLEL
         ===========================================
         input_folder  : ${params.input_folder}
         step1_out     : ${params.step1_out}
         step2_out     : ${params.step2_out}
         step3_out     : ${params.step3_out}
         """
         .stripIndent()

process step1 {
  maxForks 1
  publishDir params.step1_out
  echo true
	
  input:
    path in_file

  output:
    path "${in_file}_s1.txt"

  script:
  """
  echo Step1 for ${in_file}
  touch ${in_file}_s1.txt
  """
}

process step2 {
  maxForks 1
  publishDir params.step2_out
  echo true

  input:
    path in_file

  output:
    path "${in_file}_s2.txt"

  script:
  """
  echo Step2 for ${in_file}
  touch ${in_file}_s2.txt
  """
}

process step3 {
  maxForks 1
  publishDir params.step3_out
  echo true
  
  input:
    path in_file

  output:
    path "${in_file}_s3.txt"

  script:
  """
  echo Step3 for ${in_file}
  touch ${in_file}_s3.txt
  """
}

// This is the main workflow
workflow {

  main:
    watch_input_ch = Channel.watchPath("${params.input_folder}/*.txt", "create")
                            .until { "${it}" == "${params.input_folder}/DONE.txt" }

    step1(watch_input_ch)
    step2(step1.out)
    step3(step2.out)

}
