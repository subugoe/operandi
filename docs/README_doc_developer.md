# Developer Documentation
This document aims to guide developers who want to contribute or further develop the Operandi project.

## 1. Prerequisites
Please check the [admin](https://github.com/subugoe/operandi/tree/main/docs/README_doc_admin.md) document, section 
`Prerequisites`.

## 2. Configurations
Please check the [admin](https://github.com/subugoe/operandi/tree/main/docs/README_doc_admin.md) document, section 
`Configurations`.

## 3. Logging and Monitoring
Please check the [admin](https://github.com/subugoe/operandi/tree/main/docs/README_doc_admin.md) document, section 
`Logging and Monitoring`.

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
   or just with a make command:
   ```bash
   make start-mongo-docker
   ```
3. Start RabbitMQ Server
    ```bash
    docker compose -f ./docker-compose.yml --env-file .env up -d operandi-rabbitmq
    ```
   or just with a make command:
   ```bash
   make start-rabbitmq-docker
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

## 5. Running available tests

An instance of the MongoDB and RabbitMQ must already be running before starting the tests.

To run all available tests simply do:
```bash
make run-tests
```

It is also possible to run only tests of a specific module:
```bash
make run-tests-server
```

There is also an integration test which tests all modules with one full cycle of processing.
```bash
make run-tests-integration
```
The steps performed in the integration test are:
1. Test the availability of the Operandi server.
2. The Service broker module creates workers to listen to the different queues.
3. A small workspace is uploaded to the Operandi server using the default Harvester module credentials.
4. A workflow job is triggered with the workspace uploaded in the previous step. The workflow used is
one of the workflows provided by Operandi, i.e., `odem_workflow_with_MS`. The Operandi Server then submits the job 
request to the harvester queue. The worker responsible for that queue reads
5. The workflow job status is polled till the job succeeds, fails or timeouts.
6. If the workflow job has succeeded, the workflow job logs are downloaded.
7. Verification of existence of workspace results, i.e., existence of file group `OCR-D-OCR`.
8. Verification of existence of workflow job logs.

Note: The integration test may take up to 60 minutes depending on how fast the slurm scheduler inside the HPC 
environment starts the batch job.

For more information on testing also check the 
[tester](https://github.com/subugoe/operandi/tree/main/docs/README_doc_tester.md) documentation.

## 6. Operandi software modules
This section provides more in-depth information about the separate module packages.

TODO:

### 6.1. Operandi Server
#### 6.1.1. Server
#### 6.1.2. Files manager
#### 6.1.3. Endpoint routers
#### 6.1.4. Response models

### 6.2. Operandi Broker
#### 6.2.1. Broker
#### 6.2.2. Workers

### 6.3. Operandi Harvester

### 6.4. Operandi Client

### 6.5. Operandi Utils
#### 6.5.1. RabbitMQ
#### 6.5.2. Database
#### 6.5.3. OtoN
#### 6.5.4. HPC
##### OCR-D process workflows
##### Nextflow workflows
##### Batch Scripts

## 7. More insights regarding Operandi, Nextflow, and the GWDG HPC cluster:

TODO: Further clarify the reason for using wrapper scripts arount the batch scripts.

The `batch_submit_workflow_job.sh` is submitted to the SLURM scheduler through the front-end node of the HPC by the 
worker of the Service Broker module. The SLURM scheduler then starts the workflow job, i.e., the submitted Nextflow 
script with the number of resources and conditions specified in the request. The user/harvester currently can specify 
only the CPUs and RAM to be used with each workflow.

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
or just allocating 6 cores of any available GPU: `#SBATCH -G 6`. However, keep in mind that the allocated GPU will be 
used by all processor blocks inside the Nextflow workflow regardless if they benefit from the GPU or not.

Overall, it is very hard to estimate the required computational resources for each OCR-D processor step in the Nextflow 
workflow for efficient computations. To provide more flexible configurations, it is required to either produce the 
batch scripts dynamically or pass arguments to the batch scripts dynamically. Operandi implements the second option. 
There is already a base scratch script which receives some arguments when executed.

The `errorStrategy` and `maxErrors` directives inside the Nextflow process block could help with the dynamic allocation 
of resources when a process fails due to lack of enough resources (i.e. memory). Consider the simple example below: 
```text
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
However, keep in mind that this is not ideal and wastes resources. The preferred way is trying to always allocate enough 
amount of memory.