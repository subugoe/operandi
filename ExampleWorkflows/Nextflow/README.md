# Example Nextflow workflows

## Install Nextflow or use the VM dev environment

1. Please check the [install documentation](https://www.nextflow.io/docs/latest/getstarted.html) of Nextflow and install it on your local machine.
2. Alternatively, you could connect to our development VM (ssh cloud@141.5.99.32) and use the environment there (the development team should have an access).

## workflow1
Inside this folder there are an `input` and an `output` folder.
The `input` folder consists of 3 files, 2 of which (`input_1.txt` and `input_2.txt`) are used as an input by the workflow.

The content of the `input_1.txt` is the even integer numbers from 0 to 48 (inclusive).
The content of the `input_2.txt` is the odd integer numbers from 1 to 49 (inclusive).

The `multiplier_process.nf` and `multuplier_process_dsl.nf` files represent the same workflow.
The main difference is that the second file has DSL 2 enabled which provides a syntax extension that enables:
- implementation of functions and modules
- usage of workflow blocks

The workflow reads the content of the input files and multiplies each integer with the value of the `multiplier parameter` which is set to 2.
As a result, two output files named `multiplied_1.txt` and `multiplied_2.txt` are created inside the `output` directory.

### Notes
- The workflow expects the availability of an `output` folder and does not create one in case it is missing.
- After the workflow executes, a `work` directory is created by default. That directory holds the workspace of all processes created during the workflow execution
- Each execution has also its own log files (`.nextflow.log.*`)
- The cache and history are stored under the `.nextflow` directory.
- Make sure to clear the cache and the output files to avoid potential bugs during the testing/learning process. This could also be done automatically by using either a `beforeScript` or `afterScript` directives inside the processes (check workflow2 for more information about such directives).
- To execute the workflow use `nextflow run flow_name.nf` in the terminal (e.g. `nextflow run multuplier_process_dsl.nf`)

## workflow2
Inside this folder, there is a `complex_workflow.nf` file that represents a complex workflow execution.
The aim of it is to demonstrate some main Nextflow functionalities.

The idea behind the workflow is to create a random integer by running a bash script and writing it to a file inside the execution environment of each process.
The file names are assigned dynamically based on the channel input integer the processes receive.
In total, there are 6 processes (3 for `basic_flow1` and 3 for `basic_flow2`).
The `print_input1` and `print_input2` are there to observe the results easily.
Finally, the `integer_collector` process reads the produced integer values (by taking the output results of the `basic_flow1` and `basic_flow2` as an input) and appends them inside the `./input/integers.txt` file.

### Notes
- Processes run in parallel, so the output would not be always in the same order!
- `temp` folder is created to demonstrate how to store the produced results in a single directory specified with the `publishDir` directive inside the processes. Processes still have their files inside their workspace (i.e. inside the `work` folder).
- `integers.txt` is an output file that we would like to use as an input for further processing. Thus, the file is created inside the input directory.
- `maxForks` directive inside the `integer_collector` process sets the number of maximum instances. Useful when we want to execute a process in a sequential manner.

## workflow3
This workflow demonstrates how to run dummy OCR-D processors in parallel. For our example, we use the demo processor ocrd-vandalize.

### 1. Installation of the ocrd_vandalize processor from the source
1. Clone the repository and enter its directory
```sh
git clone https://github.com/kba/ocrd_vandalize
cd ocrd_vandalize
```
2. Create a virtual Python environment and activate it.
```sh
python3 -m venv $HOME/venv-ocrd
source $HOME/venv-ocrd/bin/activate
```
NOTE: if you change the path of the virtual environment, do not forget to set the correct environment path inside the Nextflow script!

3. Install the wheel package (if missing, e.g., `error: invalid command bdist_wheel` encountered) and the ocrd_vandalize
```sh
pip3 install wheel
make install
```
4. Check if the ocrd_vandalize is installed properly. Then deactivate the environment.
```sh
ocrd-vandalize --version
deactivate
```

### 2. Preparation of the input files for the Nextflow workflow
Execute the `prepare.sh` script inside the `workflow3` folder to prepare the input files.
```sh
cd workflow3
./prepare.sh
```

The script does the following:
1. Downloads a zip file that contains some example data.
2. Creates an `input` folder and three separate subfolders named `data1`, `data2`, and `data3`.
3. A copy of the example data is copied inside each of the subfolders.

### 3. Execution of the workflow
```sh
nextflow run workflow_with_ocrd.nf -with-report
```

The Nextflow workflow does the following:
1. Executes the ocrd-vandalize processor in parallel for each subfolder
2. An `output` directory is created with the results for each subfolder
3. HTML execution report with a summary, resource usage, and tasks is created (default report file `report.html`)

NOTE: The output results of the processors are stored inside each subfolder and a copy link is published inside the `output` directory.

### 4. Cleaning of the created files
Execute the `clean.sh` script to clean the downloaded zip, execution logs, and the created folders - `input`, `output`, `work`, `.nextflow`.

## workflow4
The 3 workflow examples demonstrate how to run OCR-D processors sequentially (`seq_ocrd_wf_single.nf`, `seq_ocrd_wf_many.nf`) and in parallel (`parallel_ocrd_wf.nf`). Refer to the previous instructions to run the workflows. Prepare the workspace for a sequential run with `prepare.sh` and for a parallel run with `prepare_parallel.sh`. Clean the produced files with `clean.sh`.

## workflow5
This workflow5 example is for the HPC environment.

## workflow6
Demonstration of the `watchPath` with `until` property.

What to do:
1. Prepare the folders structure with `./prepare.sh`
2. Execute the `pipelined_wf_v2` (version 2!) script with `$nextflow run pipelined_wf_v2`.
3. Open a second terminal window.
4. Change the working directory to `input_folder` with `cd`.
5. Create a new file `.txt` file -> `$touch a.txt`
6. Observe the results on the first terminal
7. Go back to Step 5 and repeat as many times as you wish. 
8. To finish the workflow create a text file with the name `DONE.txt`.
9. To clean the content inside the folders use `./clean.sh`

NOTES: 
1. `pipelined_wf_v1` does not work as intended. Having separate `watchPath` channels for each `step` process leads to a situation in which when the `DONE.txt` file is created inside the `input_folder` the `watch_input_ch` channel is closed without submitting that file to process `step1`. So, the `watchPath` of the `step1_out` folder gets stuck in an infinite loop since the file which ends the loop is never created! Manually creating the intended file inside the `step1_out` folder do the task, but this is not what we are trying to achieve in this example. For the same reason, `watchPath` of the `step2_out` gets stuck in an infinite loop as a chain reaction.

2. `pipelined_wf_v2` works just as intended!
