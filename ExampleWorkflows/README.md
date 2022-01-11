# Example Nextflow workflows

## Install Nextflow or use the VM dev environment

1. Please check the [install documentation](https://www.nextflow.io/docs/latest/getstarted.html) of Nextflow and install it on your local machine.
2. Alternatively, you could connect to our development VM (ssh cloud@141.5.105.17) and use the environment there (the team developers should have access).

## workflow1
Inside this folder there are an `input` and an `output` folder.
The `input` folder consists of 3 files, 2 of which (`input_1.txt` and `input_2.txt`) are used as an input by the workflow.

The content of the `input_1.txt` are the even integer numbers from 0 to 48 (inclusive).
The content of the `input_2.txt` are the odd integer numbers from 1 to 49 (inclusive).

The `multiplier_process.nf` and `multuplier_process_dsl.nf` files represent the same workflow.
The main difference is that the second file has DSL 2 enabled which provides a syntax extension that enables:
- implementation of functions and modules
- usage of workflow blocks

The workflow reads the content of the input files and multiplies each integer with the value of the `multiplier parameter` which is set to 2.
As a result, two output files named `multiplied_1.txt` and `multiplied_2.txt` are created inside the `output` directory.

### Notes
- The workflow expects the availability of an `output` folder and do not create one in case it is missing.
- After the workflow executes, a `work` directory is created by default. That directory holds the work space of all processes created during the workflow execution
- Each execution has also its own log files (`.nextflow.log.*`)
- The cache and history are stored under the `.nextflow` directory.
- Make sure to clear the cache and the output files to avoid potential bugs during the testing/learning process. This could also be done automatically be using either a `beforeScript` or `afterScript` directives inside the processes (check workflow2 for more information about such directives).

## workflow2
Inside this folder there is a `complex_workflow.nf` file that represents a complex workflow execution.
The aim of it is to demonstrate some main Nextflow functionalities.

The idea behind the workflow is to create a random integer by running a bash script and write it to a file inside the execution environment of each process.
The file names are assigned dynamically based on the channel input integer the processes receive.
In total, there are 6 processes (3 for `basic_flow1` and 3 for `basic_flow2`).
The `print_input1` and `print_input2` are there to observe the results easily.
Finally, the `integer_collector` process reads the produced integer values (by taking the output results of the `basic_flow1` and `basic_flow2` as an input) and appends them inside the `./input/integers.txt` file.

### Notes
- Processes run in parallel, so the output would not be always in the same order!
- `temp` folder is created to demonstrate how to store the produced results in a single directory specified with the `publishDir` directive inside the processes. Processes still have their files inside their work space (i.e. inside the `work` folder).
- `integers.txt` is an output file that we would like to use as an input for further processing. Thus, the file is created inside the input directory.
- `maxForks` directive inside the `integer_collector` process sets the number of maximum instances. Useful when we want to execute a process in a sequential manner.
