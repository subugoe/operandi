# OPERANDI
This is the OPERANDI project's repository. The Readme file is still a draft and under construction.
The file may be slightly outdated. Will be updated after integrating the OCR-D WebApi.

## 1. Introduction
OPERANDI is one of the implementation projects funded by the DFG initiative OCR-D. The main goal of OCR-D is the conceptual and technical preparation of the full-text transformation of the 16th to 18th-century prints published in the German language area. The task of automatic full-text recognition is broken down into individual process steps, which can be reproduced in the open-source OCR-D software. This makes it possible to create optimal workflows for the prints to be processed, and thus generate scientifically usable full texts.

The goal of OPERANDI is to develop and build an OCR-D-based implementation package for mass full-text capture with improved throughput while improving the quality of the results. At the same time, the goal is that the implementation package can also be used by other projects and institutions with comparable requirements. Two scenarios were identified during the pilot. In the first scenario, OCR generation is to take place for works that have already been digitized, resulting in mass full-text capture. In the second scenario, OCR generation for new works to be digitized will take place as part of the digitization process.

## 2. Architecture
<picture>
  <img src="https://raw.githubusercontent.com/subugoe/operandi/main/OPERANDI_arch.png">
</picture>

## 3. Installation of OPERANDI from source
#### 3.1. Clone the repository and enter its directory.
```sh
git clone git@github.com:subugoe/operandi.git
cd operandi
```

#### 3.2. Install dependencies
```sh
sudo apt-get update
sudo apt-get -y install make
sudo make deps-ubuntu
```

#### 3.3. Create a virtual Python environment and activate it.
```sh
python3 -m venv $HOME/venv-operandi
source $HOME/venv-operandi/bin/activate
```

#### 3.4. Install the modules of OPERANDI.
```sh
make install-dev
```

## 4. Configurations

Select either of the two options and fulfill the requirements.

#### 4.1 Option 1: The service broker executes workflows on the local host

<details>
<summary> 4.1.1 Requirements </summary>

1. OCR-D Software, check [here](https://ocr-d.de/en/setup) for more details. 
For simplicity, just pull the docker image of `ocrd/all:maximum`. 
As the tag hints, this will download the entire OCR-D software (~13.5GB).
```sh
docker pull ocrd/all:maximum
```

2. Nextflow installed locally, check [here](https://www.nextflow.io/docs/latest/getstarted.html) for more details.
```sh
curl -s https://get.nextflow.io | bash
chmod +x nextflow
mv nextflow /usr/local/bin/
nextflow -v
```

</details>

<details>
 <summary> 4.1.2 Configurations </summary>
By default the service broker is configured to run locally. 
No further configurations needed.
</details>

#### 4.2 Option 2: The service broker executes workflows in the HPC environment

<details>
<summary> 4.2.1 Requirements </summary>

1. GWDG credentials, check [here](https://docs.gwdg.de/doku.php?id=en:services:application_services:high_performance_computing:account_activation).
2. Access to the HPC environment, check [here](https://docs.gwdg.de/doku.php?id=en:services:application_services:high_performance_computing:connect_with_ssh).
</details>

<details>
<summary> 4.2.2 Configurations </summary>

1. Set the HPC related credentials `HPC_USERNAME` and `HPC_KEY_PATH` inside the 
`operandi/src/service_broker/service_broker/config.toml` file of the 
service broker module.

2. Reinstall the OPERANDI modules to save the changes of the previous step
```sh
make install-dev
```

Soon there will be a more convenient way to configure things 
and reinstallation of modules will not be needed.
</details>

## 5. Executing one full cycle of OPERANDI

Executing steps `5.1` and `5.2` for the first time will take more time - downloading and building.

#### 5.1 Start the MongoDB docker container
```bash
make start-mongo-docker
```

#### 5.2 Start the RabbitMQ docker container
```bash
make start-rabbitmq-docker
```

<details>
 <summary> Check if MongoDB and RabbitMQ are running: </summary>

`sudo lsof -i -P -n | grep LISTEN` or `docker ps`

By default, the MongoDB is listening on port 27018 and 
RabbitMQ is listening on ports 5672, 15672, and 25672.
```sh
docker-pr 102316  root  4u  IPv4 635588  0t0  TCP *:27018 (LISTEN)
docker-pr 102323  root  4u  IPv6 644201  0t0  TCP *:27018 (LISTEN)
docker-pr 103097  root  4u  IPv4 637506  0t0  TCP *:25672 (LISTEN)
docker-pr 103103  root  4u  IPv6 646574  0t0  TCP *:25672 (LISTEN)
docker-pr 103116  root  4u  IPv4 648464  0t0  TCP *:15672 (LISTEN)
docker-pr 103122  root  4u  IPv6 630453  0t0  TCP *:15672 (LISTEN)
docker-pr 103134  root  4u  IPv4 642880  0t0  TCP *:5672 (LISTEN)
docker-pr 103141  root  4u  IPv6 642885  0t0  TCP *:5672 (LISTEN)
```
</details>

#### 5.3 Start the Operandi server
Open a new terminal, activate the virtual Python environment created in `step 3.3`, and 
start the Operandi server instance:
```bash
source $HOME/venv-operandi/bin/activate
make start-server-native
```

Note: Starting the Operandi server for the first time creates a RabbitMQ message queue 
used to communicate with the Operandi broker.

#### 5.4 Start the Harvester
As in `step 5.3`, activate the environment, then start the harvester.
```bash
source $HOME/venv-operandi/bin/activate
make start-harvester-native
```
The harvesting module will harvest only a single mets url workspace by default.
It is also possible to harvest more than one mets url. 
To do so start the harvester by setting the desired limit.
Currently, there are no limit checks, so do not use a big `N` value.
```bash
operandi-harvester start --limit N
```

Note: Starting the Harvester for the first time creates a RabbitMQ message queue 
used to communicate with the Operandi broker.

#### 5.5 Start the Operandi broker
Depending on the configuration in `step 3`, there are two options. 
To run a service broker instance that executes workflows locally:

As in `step 5.3`, activate the environment, and start one of the broker instances.

<details>
 <summary> Local instance </summary>

```bash
source $HOME/venv-operandi/bin/activate
make start-broker-native
```
</details>

<details>
 <summary> HPC instance - disabled till we have a proper authentication </summary>
</details>

Note: The broker listens for new requests comming from the 2 RabbitMQ message queues
created in `step 5.3` and `step 5.4`.

Warning: Running the Operandi broker first before Operandi Server and Harvester may result in errors. 
As mentioned in the previous Notes, the respective message queues used for communication are created 
by the Operandi server and the Harvester. 
The Operandi broker does not create the queues if they're missing.

#### 5.6 Interactive API documentation

Check the interactive API documentation of the Operandi server once there is a running server instance (http://localhost:8000/docs).
Operandi reuses the provided API from OCR-D and extends it.

1. OCR-D WebAPI [spec](https://github.com/OCR-D/spec/blob/master/openapi.yml)
2. OCR-D WebAPI [swagger](https://app.swaggerhub.com/apis/kba/ocr-d_web_api/0.0.1#/).
3. OCR-D WebAPI [repo](https://github.com/OCR-D/ocrd-webapi-implementation).

#### 5.7 Curl requests
These are the curl requests we support in the alpha release of Operandi, e.g., 
the `default` tag in the interactive API documentation.

<details>
 <summary> 1. Post a workspace, parameters: `METS URL` and `workspace_id`. </summary>

```sh
E.g.:
mets_url=https://content.staatsbibliothek-berlin.de/dc/PPN631277528.mets.xml
workspace_id=PPN631277528
```
`Warning`: Note that in `mets_url=VALUE` the `:` and `/` are replaced with `%3A` and `%2F`, respectively, in the curl command below.
Do not just copy and paste a browser link.

```sh
curl -X 'POST' 'http://localhost:8000/mets_url/?mets_url=https%3A%2F%2Fcontent.staatsbibliothek-berlin.de%2Fdc%2FPPN631277528.mets.xml&workspace_id=PPN631277528'
```

The `workspace_id` is modified with a timestamp suffix, i.e., `workspace_id_{timestamp}`

Once you submit the `mets_url` and the `workspace_id`, the service broker creates a directory named `workspace_id_%Y%m%d_%H%M`,
downloads the mets file, and the images of fileGrp `DEFAULT` inside the mets file.
Then the broker triggers a Nextflow workflow on that workspace using the base Nextflow script inside the service broker
(the base Nextflow script runs only the binarization processor). 

Soon, we will support a way to provide the desired `fileGrp` to be used. 
Moreover, we will offer several ready-to-run Nextflow scripts to choose from instead of running just the base Nextflow script.
In addition, there will be a way to provide an OCR-D process workflow text file which will be converted to a Nextflow script.
Check [here](https://github.com/MehmedGIT/OtoN_Converter) for additional information on the OtoN (OCR-D to Nextflow) converter. 

</details>

<details>
 <summary> 2. List available workspaces.</summary> 

It shows all `workspace_id`'s currently available on the Operandi Server. E.g.:
```sh
curl -X 'GET' 'http://localhost:8000/workspaces/'
```

</details>


<details>
 <summary> 3. Download a workspace + workflow results </summary>

Download the zip of a `workspace_id_timestamp`. Suggestion: first list the available `workspace_id`'s to find your 
`workspace_id` with the timestamp suffix. Then replace `workspace_id=VALUE` appropriately.
Set the `output` path of the zip appropriately, i.e., the download location of the zip.
```sh
curl -X 'GET' 'http://localhost:8000/workspaces/workspace_id?workspace_id=PPN631277528_20220728_1700' --output ~/operandi_results/PPN631277528.zip
```

The zip file includes the following:
1. A `bin` directory with the `ocrd-workspace` and the executed base Nextflow script.
2. A `work` directory that has detailed information on the processes executed with Nextflow (logs, outputs, errors, etc.). 
This is especially useful for debugging!
3. A Nextflow report with execution details such as execution duration and used resources: `report.html` 
4. An `output.txt` that holds the `stdout` of the current Nextflow execution.

</details>

## 6. Solutions to potential problems

This section provides solutions for potential problems that may arise.

<details>
 <summary> 1. Authentication errors using SSH when starting the `service-broker-hpc`.</summary>

A potential reason for that error could be that your private key was not added to the SSH Agent.

Solution:
```sh
eval `ssh-agent -s`
ssh-add /path/to/your_key
```

The first command activates the SSH Agent (in case it is not active).

The second command adds the private key to the SSH Agent. 
The given path for the private key is the path inside the development VM. 
Make sure to provide the correct path for your local installation.

</details>

<details>
 <summary> 2. Downloading images referenced inside the METS file fails with an HTTP request exception.</summary>

This is a known problem. This usually happens with METS files coming from the GDZ. 

The URLs to the images inside the mets file sometimes trigger server-side error exceptions, e.g., `Exception: HTTP request failed: URL (HTTP 500)`

- Bad solution: Find-all and replace `http://gdz-srv1.` with `https://gdz.` inside the mets file.
- Better Solution: Try a METS file URL from another library. E.g.,
```sh
https://content.staatsbibliothek-berlin.de/dc/PPN631277528.mets.xml
```
```sh
curl -X 'POST' 'http://localhost:8000/mets_url/?mets_url=https%3A%2F%2Fcontent.staatsbibliothek-berlin.de%2Fdc%2FPPN631277528.mets.xml&workspace_id=PPN631277528'
```
</details>

## 7. Some insights regarding Operandi, Nextflow, and GWDG HPC cluser:
Consider the following 3 files and their contents:
<details>
<summary> batch_script.sh </summary>

```bash
#!/bin/bash
#SBATCH --partition medium
#SBATCH --constraint scratch
#SBATCH --cpus-per-task 4
#SBATCH --mem 16G
#SBATCH --output /home/users/mmustaf/jobs_output/job-%J.txt

# clear the environment then load singularity and nextflow
module purge
module load singularity  # loads "git" and "go" as well
module load nextflow  # loads "openjdk" as well

... 
# managing the creation of directories and moving files here 
...

# execute the main Nextflow script
nextflow run ./simple.nf --file_group "DEFAULT" --volumedir "path/to/workspace"

... 
# transferring the results from the scratch storage to somewhere else
# cleaning no longer needed files
...
```
</details>

<details>
<summary> nextflow.config </summary>

```nextflow
singularity {
  enabled = true
  // Path to the singularity SIF file of the OCR-D all software
  cacheDir = '/scratch1/users/mmustaf/singularityCache'
}

executor {
  name = 'slurm'
  // ...
  // Other SLURM related configurations 
  // ...
}

process {
  withName: download_workspace {
    cpus = 1
    memory = 8.GB
    queue = 'medium'  // partition
  }
  withName: ocrd_cis_ocropy_binarize {
    cpus = 4
    memory = 16.GB
  }
  withLabel: active_gpu {
     queue = 'gpu'  // partition
     containerOptions = '--nv'  // to make GPU drivers accessible in the singularity container
  }
}
```
</details>

<details>
<summary> simple.nf </summary>

```nextflow
nextflow.enable.dsl=2

params.file_group = ""
params.volume_dir = ""
// $projectDir is the directory where this NF script is located
params.mets_path = "$projectDir/ocrd-workspace/mets.xml"

process download_workspace {
  input:
    val file_group
  output:
    val file_group

  script:
  """
  singularity exec --bind ${params.volume_dir} docker://ocrd/all:maximum ocrd workspace find --file-grp ${file_group} --download --wait 1
  """
}

process ocrd_cis_ocropy_binarize {
  label 'active_gpu'
  input:
    path mets_file 
    path dir_name
  output:
    val "OCR-D-BIN"
  
  script:
  """
  singularity exec --bind ${params.volume_dir} docker://ocrd/all:maximum ocrd-cis-ocropy-binarize -m ${mets_file} -I ${dir_name} -O "OCR-D-BIN"
  """
}

// This is the main workflow
workflow {
  main:
    download_workspace(params.file_group)
    ocrd_cis_ocropy_binarize(params.mets_path, download_workspace.out)
}
```
</details>

NOTE: The examples are not tested/executed, and are provided as a reference.

1. The `batch_script.sh` is submitted to the SLURM scheduler through the front-end node of the HPC by the Service Broker module worker. The SLURM scheduler then starts the workflow job, i.e., the submitted Nextflow script with the number of resources and conditions specified inside the batch script.
2. The SLURM executor of Nextflow then manages the allocation of separate jobs for each Nextflow process by talking to the SLURM scheduler of HPC and requesting resources specified inside the `nextflow.config` file. The upper limit for a resource is the resource allocated when executing the Nextflow script. In this example, 4 CPUs and 16GBs of memory.
3. With the `nextflow.config` (check [here](https://www.nextflow.io/docs/latest/config.html#config-scopes) regarding the scopes) it's possible to configure resources to be allocated for each step inside the NF script. So, that single configuration file could be used with any number of NF scripts as long as 1) the process names are consistent between the two files, or 2) specific labels are added inside the NF script inside processes as a directive to tag them into a group.
4. Using the GPU resource is possible when running the job inside the GPU partition (according to the [GWDG documentation](https://docs.gwdg.de/doku.php?id=en:services:application_services:high_performance_computing:running_jobs_slurm), I don't know about other HPC environments). So inside the batch script, the partition parameter should be replaced and the GPU unit specified with format `name:cores`:
```bash
#SBATCH --partition gpu
#SBATCH -G gtx1080:6
```
or just allocating 6 cores of any available GPU: `#SBATCH -G 6`. 

Overall, it's very hard to estimate the required resources for each OCR-D processor step in the OCR-D workflow based on the provided workspace (images). To provide more flexible configurations, it is required to produce the batch scripts and the nextflow config files dynamically. 

The `errorStrategy` and `maxErrors` directives inside the process block could help with the dynamic allocation of resources when a process failes due to lack of enough resources (i.e. memory). These directives can, of course, be specified in a `nextflow.config` file as well in order to group the error strategy and max retries for a group of processes. Consider this simple example below: 
```nextflow
process binarization {
  memory { 2.GB * task.attempt }
  errorStrategy { task.exitStatus in 137..140 ? 'retry' : 'terminate' }
  maxRetries 3

  script:
  """
  call the ocr-d processor here
  """
}
```

The binarization process is executed and if the task fails due to out of memory error, the next execution attempts will increase the memory allocation and try again. Also note that the task exit status codes are not standard and can change depending on the resource manager used in the HPC cluster.
