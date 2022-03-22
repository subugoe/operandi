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
- To execute the workflow use `nextflow run flow_name.nf` in the terminal (e.g. `nextflow run multuplier_process_dsl.nf`)

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

## workflow3
This workflow demonstrates how to run dummy OCR-D processors in parallel. For our example we use the demo processor ocrd-vandalize.

### 1. Installation of the ocrd_vandalize processor from source
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
NOTE: if you change the path of the virtual environment, do not forget to set the correct environment path inside the nextflow script!

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
3. HTML execution report with summary, resource usage, and tasks is created (check the example `report.html`)

NOTE: The output results of the processors are stored inside each subfolder and a copy link is published inside the `output` directory.

### 4. Cleaning of the created files
Execute the `clean.sh` script to clean the downloaded zip, execution logs, and the created folders - `input`, `output`, `work`, `.nextflow`.

## workflow4
The 3 workflow examples demonstrate how to run OCR-D processors sequentially (`seq_ocrd_wf_single.nf`, `seq_ocrd_wf_many.nf`) and in parallel (`parallel_ocrd_wf.nf`). Refer to the previous instructions to run the workflows. Prepare the workspace for sequential run with `prepare.sh` and for parallel run with `prepare_parallel.sh`. Clean the produced files with `clean.sh`.


