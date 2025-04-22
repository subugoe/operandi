# Developer Documentation
This document aims to guide developers who want to contribute or further develop the Operandi project.

## 1. Prerequisites
TODO:

## 2. Configurations
TODO:

## 3. Logging and Monitoring
TODO:

## 4. Local execution

### 4.1. Deploy all modules in docker
After adapting the `docker.env` file in the repo, simply run:
```shell
docker compose -f ./docker-compose_image_based.yml --env-file docker.env up -d
```

There are 2 identical docker compose files. The one used in the command above downloads the prebuilt remote docker 
images of the Operandi Server and Operandi Broker. The other one, `docker-compose.ymp`, builds docker images from the 
source code. 

### 4.2. Deploy modules separately
If either the Operandi Server or Operandi Broker fails to run, you may want to try running them locally.

<details>
<summary> Install Operandi from source </summary>

1. Install dependencies:
    ```sh
    sudo apt-get update && 
    sudo apt-get install -y make &&
    sudo make deps-ubuntu
    ```
2. Create a virtual Python environment and activate it:
    ```sh
    python3 -m venv $HOME/venv-operandi &&
    source $HOME/venv-operandi/bin/activate
    ```
3. Install Operandi modules
    ```sh
    make install-dev
    ```

</details>

<details>
<summary> Deploy modules </summary>

1. Stop and remove previously deployed docker modules:
    ```bash
    docker compose -f ./docker-compose_image_based.yml --env-file docker.env down --remove-orphans
    ```
2. Start MongoDB:
    ```bash
    docker compose -f ./docker-compose.yml --env-file .env up -d operandi-mongodb
    ```
3. Start RabbitMQ Server
    ```bash
    docker compose -f ./docker-compose.yml --env-file .env up -d operandi-rabbitmq
    ```
4. Start Operandi Server
    ```bash
    make start-server-native
    ```
5. Start Operandi Broker
    ```bash
    make start-broker-native
    ```

Pay attention that in the docker calls above the `.env` file is used. Since the server and broker are not deployed with 
docker compose they are not part of the network created by the docker compose. Thus, the address of the MongoDB and 
RabbitMQ is just the localhost and not the docker network.
</details>

### 4.3. Interactive API documentation

Check the interactive API documentation of the Operandi server once there is a running server 
instance (http://localhost/docs). 

Operandi implements the Web API from OCR-D and extends it.

1. OCR-D WebAPI [spec](https://github.com/OCR-D/spec/blob/master/openapi.yml)
2. OCR-D WebAPI [swagger](https://app.swaggerhub.com/apis/kba/ocr-d_web_api/0.0.1#/).
3. OCR-D WebAPI [repo](https://github.com/OCR-D/ocrd-webapi-implementation).

## 5. Operandi software modules
TODO:

## 6. More insights regarding Operandi, Nextflow, and GWDG HPC cluster:
The `submit_workflow_job.sh` is submitted to the SLURM scheduler through the front-end node of the HPC by the worker of 
the Service Broker module. The SLURM scheduler then starts the workflow job, i.e., the submitted Nextflow script with 
the number of resources and conditions specified in the request. The user/harvester currently can specify only the CPUs 
and RAM to be used with each workflow.

The SLURM executor of Nextflow then manages the allocation of separate jobs for each Nextflow process by talking to the 
SLURM scheduler of HPC and requesting resources specified inside the Nextflow workflow file. The upper limit for a 
resource is the resource allocated when executing the Nextflow script.

Using the GPU resource is possible when running the job inside the GPU partition (according to the 
[GWDG documentation](https://docs.gwdg.de/doku.php?id=en:services:application_services:high_performance_computing:running_jobs_slurm), this may be different for other HPC environments). So inside the batch script, the partition 
parameter should be replaced and the GPU unit specified with format `name:cores`:
```bash
#SBATCH --partition gpu
#SBATCH -G gtx1080:6
```
or just allocating 6 cores of any available GPU: `#SBATCH -G 6`. 

Overall, it is very hard to estimate the required computational resources for each OCR-D processor step in the Nextflow 
workflow for efficient computations. To provide more flexible configurations, it is required to either produce the 
batch scripts dynamically or pass arguments to the batch scripts dynamically. Operandi implements the second option. 
There is already a base scratch script which receives some arguments when executed.

The `errorStrategy` and `maxErrors` directives inside the process block could help with the dynamic allocation of 
resources when a process fails due to lack of enough resources (i.e. memory). Consider the simple example below: 
```shell
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