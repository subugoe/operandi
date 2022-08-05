// enables a syntax extension that allows definition of module libraries
nextflow.enable.dsl=2

// pipeline parameters 
params.reads = "$projectDir/input/input_*.txt"
params.indir = "$projectDir/input/"
params.outdir = "$projectDir/output/"
params.multiplier = 2

// log pipeline parameters to the console
log.info """\
         O P E R A N D I - T E S T   P I P E L I N E 1
         ===========================================
         reads      : ${params.reads}
         indir      : ${params.indir}
         outdir     : ${params.outdir}
         multiplier : ${params.multiplier}
         """
         .stripIndent()

// reads integers separated with a white space character inside a line
// then multiplies them with the value of the multiplier parameter
def multiply_line(line) {
   // splits the read line into strings, each string is a string format integer
   // then converts the string format integers to integers
   def integerList = line.split("\\s+").collect{it.toInteger()}
      
   // another way to accomplish the same result 
   // as the line above is to use a Java function:
   // integerList = line.split("\\s+").collect { java.lang.Integer.valueOf(it) }
      
   // multiplies each integer with the multiplier parameter
   def multipliedList = integerList.collect{it*params.multiplier}
      
   // joins the list of multiplied integers into a single string line 
   // with a delimiter whitespace between the values
   String multipliedString = multipliedList.join(' ') + '\n'
   
   // returns multipliedString
   // functions implicitly return the result of the last evaluated statement
   // it is also possible to return results on any line with the "return" keyword
}

/*
 * Reads the content of an input file,
 * multiplies each integer value inside with the multiplier parameter,
 * and outputs the result in an output file.
 * An instance of the process is created for each file inside the input_file_ch channel.
 */
// DSL separates the definition of a process from its invocation
// The process definition follows the usual syntax
// The only difference is that the "from" and "into" channel declarations are not possible
process multiplier_process {

   // the input channel is passed as a process parameter
   input: 
   path x
   
   // the exec: makes possible to execute native code (Groovy) other than system scripts
   exec:
   // get the start time of the process by invoking external java function
   startTime = java.time.LocalDateTime.now()
   
   // x is the name of the input file
   // params.indir is the input directory path
   sourceReader = file("${params.indir}${x}").newReader()
   
   // the name of the output file is x with prefix "multiplied_"
   // params.outdir is the output directory path
   destWriter = file("${params.outdir}multiplied_${x}").newWriter()
   
   String line
   // reads lines from the source file till EOF is reached
   while(line = sourceReader.readLine()) {
   
      // does the multiplications
      String multiplied_line = multiply_line(line)
      
      // writes the line to the destination file
      destWriter.write(multiplied_line)
   }
   
   // close the file instances
   sourceReader.close()
   destWriter.close()

   // get the end time of the process by invoking external java function
   endTime = java.time.LocalDateTime.now()
   
   println "Process started at: ${startTime} ended at: ${endTime}"
}

// a workflow that do not have a name is considered as the main workflow
// the main workflow is executed implicitly
workflow {
   // all files that match the params.reads pattern are loaded to the channel
   input_file_ch = Channel.fromPath(params.reads)
   
   // a process component can be invoked only once in the same workflow context
   multiplier_process(input_file_ch)
}

