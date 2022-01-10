// enables a syntax extension that allows definition of module libraries
nextflow.enable.dsl=2

// pipeline parameters 
params.indir = "$projectDir/input/"
params.outdir = "$projectDir/output/"

all_integers = []

// log pipeline parameters to the console
log.info """\
         O P E R A N D I - T E S T   P I P E L I N E 2   
         ===========================================
         indir      : ${params.indir}
         outdir     : ${params.outdir}
         """
         .stripIndent()

// input: a value channel containing integers
// a separate instance of the process is executed for each integer inside the input channel
// 
// effect: 
// - creates output files with names matching the pattern "input_num_*.txt"
// - * is replaced by the received input integer from the input channel
// - each file contains a random integer produced by the system
// 
// output: creates two output channels
process input_creator1 {

   input:
   val number_of_this_instance

   // if we omit the "output" block, then no output channel will be created
   // input_creator.out would not work, however, the output files are still created!

   output:
   env INTEGER_NUM
   file "input_num_*.txt" // a file with a such name must be created within the shell script!
   // once the process instance finishes its execution
   // each output is accessed from the outside with an index
   // e.g. input_creator.out[0] accesses the file output
   
   
   // RANDOM is a system variable and accessed with a $ prefix
   // number is accessed with the pattern: !{*}, where the * is the variable name
   // the only way to assign to env variables is to use a shell: block with a shell script
   shell:
   '''
   echo $RANDOM > input_num_!{number_of_this_instance}.txt
   INTEGER_NUM=$(cat input_num_!{number_of_this_instance}.txt)
   '''
}

// same as the process above, but it returns a tuple output channel
process input_creator2 {

   input:
   val number

   output:
   tuple env(INTEGER_NUM), file("input_num_*.txt")

   shell:
   '''
   echo $RANDOM > input_num_!{number}.txt
   INTEGER_NUM=$(cat input_num_!{number}.txt)
   '''
}

// prints the file names and their content received from the input channels
process print_input1 {

   input:
   val integer_num
   path file_name
   
   // In the native code (Groovy) execution (exec: block)
   // the variables are accessed with the pattern: ${*}
   exec:
   println "print_input1: [${integer_num}, ${file_name}]"

}

// same as the process above, but uses a tuple input channel
// also instead of a native execution, a bash script is used
process print_input2 {
   echo true // echo commands are disabled by default, set true to print to console

   input:
   tuple val(integer_num), path(file_name)
   
   // since the tuple variant has less flexibility in comparison to the separate channels
   // this process additionaly separates the tuple and produces separate channels
   output:
   val integer_num
   path file_name
   
   script:
   """
   echo -n "print_input2: [${integer_num}, ${file_name}]"
   """
}

workflow basic_flow1 {

   // take: data (channel data structure)
   // the block is used when the workflow takes an input data

   // the main body of the workflow
   main:
      // Create a value channel with 3 values
      numbers_ch = Channel.of(1, 2, 3)
   
      // assign the input channel of the input_creator process
      input_creator1(numbers_ch)
      // 3 independent process instances are created for each value inside numbers_ch
   
      // Viewing (printing) the content of the output channel
      // input_creator1.out[0].view() // - returns the values
      // input_creator1.out[1].view() // - returns the file names (abs paths)
      // input_creator1.out.view()    // - returns an error -> not a valid statement
   
      print_input1(input_creator1.out)
      // The parameter passed as an input above 
      // contains the results of all input_creator1 instances
   
   // sends the output channels of the print_input1 as output channels of this workflow
   emit:
      input_creator1.out[0]
      input_creator1.out[1]
      // input_creator1.out // - returns an error!
}

workflow basic_flow2 {

   // take: data (channel data structure)
   // the block is used when the workflow takes an input data

   main:
      // Create a value channel with 3 values
      numbers_ch = Channel.of(4, 5, 6)
   
      // assign the input channel of the input_creator process
      input_creator2(numbers_ch)
      // 3 independent process instances are created for each value inside numbers_ch
   
      // Viewing (printing) the content of the output channel 
      // input_creator2.out[0].view() // - returns the values and file names (abs paths) as a tuple
      // input_creator2.out[1].view() // - returns null
      // input_creator2.out.view()    // - returns the values and file names (abs paths) as a tuple
   
      print_input2(input_creator2.out)
      // The parameter passed as an input above 
      // contains the results of all input_creator2 instances

   // sends the output channel of the print_input2 as an output channel of this workflow
   // this time we have assigned a specific name to the output channel of this workflow
   emit:
      // input_creator2.out    // - sends the tuple as an output channel
      // input_creator2.out[0] // - has the same effect as the line above
      
      // For flexibility reasons we use the separate output channels produced with print_input2
      print_input2.out[0]
      print_input2.out[1]
}

// integer collecting flow
// collects all integers produced so far
// return: a single channel containing all integers

// the function version of the integer_collector
/*
def integer_collector (ch1_data, ch2_data){

   destWriter = file("${params.indir}integers.txt").newWriter()

   ch1_data.subscribe {  
      // all_integers.add(it)
      destWriter.append(it + '\n')
   }
   ch2_data.subscribe { 
      // all_integers.add(it)
      destWriter.append(it + '\n')
   }
   
   //destWriter.close()
}
*/

// WE WOULD NOT LIKE TO EXECUTE THIS AS A PROCESS
// SINCE A NEW PROCESS INSTANCE IS CREATED FOR EACH X AND Y PAIR

// the process version of the integer_collector
/*
process integer_collector {
   
   input:
      val x // from ch1_data
      val y // from ch2_data
      
   exec:
      destWriter = file("${params.indir}integers.txt").newWriter()
      println "The x is ${x} and the y is ${y}"
      destWriter.append(x + '\n')
      destWriter.append(y + '\n')
      destWriter.close()
}
*/

// the workflow version of the integer_collector
workflow integer_collector {

   take:
      ch1_data
      ch2_data

   // Since the 
   main:
      destWriter = file("${params.indir}integers.txt").newWriter()

      ch1_data.subscribe {  
         // all_integers.add(it)
         destWriter.append(it + '\n')
      }
      ch2_data.subscribe { 
         // all_integers.add(it)
         destWriter.append(it + '\n')
      }
      
      // destWriter.close()
   
}

// This is the main workflow
workflow {

   main:
      basic_flow1()
      basic_flow2()
      
      // in theory the integer_collector2 should wait here
      // for basic_flow1 and basic_flow2 to finish their execution
      // since we pass their output as an input
      // however, this seems to not be the case
      
      integer_collector(basic_flow1.out[0], basic_flow2.out[0])

}














