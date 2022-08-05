# Example CWL workflows
Both sequential and parallel workflows execute only 2 OCR-D processors: `ocrd-cis-ocropy-binarize` and `ocrd-anybaseocr-crop`. 
The objective is to compare CWL scripts to Nextflow scripts.

## 1. Virtual Python environment
If you already have a Python environment with installed OCR-D software then skip 1.1 and 1.2.

1.1 Create a new Python environment
```sh
python3 -m venv $HOME/venv-ocrd
```

1.2 Install the OCR-D software
Check the [repository](https://www.nextflow.io/docs/latest/getstarted.html) of OCR-D for more details.

1.3 Activate the Python environment
```sh
source $HOME/venv-ocrd/bin/activate
```

## 2. Install CWL
1. Easy install with pip: `pip install cwltool cwlref-runner`
2. Please check the [repository](https://www.nextflow.io/docs/latest/getstarted.html) of CWL for more details.

## 3. Execute the examples

3.1 Execute the sequential workflow
```sh
./prepare.sh
cwl-runner sequential_workflow.cwl sequential_params.yml
```

3.2 Execute the parallel workflow
```sh
./prepare_parallel.sh
cwl-runner --parallel parallel_workflow.cwl parallel_params.yml
```

3.3 Clean the workspace created with `./prepare.sh` or `./prepare_parallel.sh` before running again
```sh
./clean.sh
```
