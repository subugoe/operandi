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
This section provides more in-depth information about the separate module packages:
- Operandi Server (6.1.)
- Operandi Broker (6.2.)
- Operandi Harvester (6.3.)
- Operandi Client (6.4.)
- Operandi Utils (6.5.)

### 6.1. Operandi Server

The Operandi server is designed to manage, process, and respond to requests from clients (users or machines). 
Conceptually, the server is divided into 4 subcomponents:
- the main Uvicorn application (the server)
- the files manager
- endpoint routers
- response models

#### 6.1.1. Server
The server application is developed using Python 3.10 and the FastAPI framework, providing a high-performance, 
asynchronous web API built on top of Starlette and Pydantic. It supports asynchronous request handling using Python’s 
`async` and `await` syntax, enabling efficient concurrency and scalability under load. FastAPI's integration with 
`Pydantic` ensures robust data validation and parsing, while automatically generating interactive API documentation 
through `Swagger UI` and `ReDoc`. The application follows a modular architecture, with components organized into routers, 
models, and services to enhance maintainability and promote clean separation of concerns. Middleware is used for logging, 
authentication, and exception handling, allowing consistent processing of all endpoints. The application is deployed 
using an ASGI server - Uvicorn, and is capable of serving as a backend for handling RESTful API requests, user 
authentication, background processing, and integration with external services, i.e., the MongoDB and the RabbitMQ.

The `server.py` file contains the main application logic, while `server_utils.py` defines supporting utility functions 
to keep the core server file clean and focused on high-level behavior. Upon invoking the `run` method, the 
`startup_event` handler is automatically executed. During startup, the logging system is reconfigured to enforce a 
consistent format across all third-party libraries. Necessary directories and the primary server log file are created, 
followed by the initialization of default admin and harvester credentials (as defined in the environment file). 
Production workflows are then generated and stored in the appropriate server-side locations. After setup, all API 
endpoint routers are registered with the FastAPI application. Conversely, the `shutdown_event` handler provides a hook 
for performing any required cleanup operations when the application terminates.

#### 6.1.2. Files manager
The files manager module, `files_manager.py`, is responsible for handling all server-side file operations in a 
structured manner. It provides a centralized interface for reading, writing, moving, deleting, and organizing files used 
by the server application. The module abstracts low-level file system interactions to ensure consistency and reduce code 
duplication across the codebase. It supports path validation, automatic directory creation, and error handling to prevent 
common I/O issues. The files manager plays a critical role in managing temporary and persistent data, supporting 
workflows that involve uploading, processing, or storing user-generated or system-generated content. Four different base 
directories are created: `workspaces`, `workflows` `worfklow jobs`, and `oton conversions`.

#### 6.1.3. Endpoint routers
The server endpoints define the HTTP interface through which clients interact with the application. Implemented using 
FastAPI's routing system, each endpoint corresponds to a specific URL path and HTTP method, handling operations such as 
data retrieval, creation, update, and deletion. The endpoints are organized into modular router definitions to separate 
concerns and improve maintainability. Each route is equipped with request validation using `Pydantic` models, ensuring 
that incoming data conforms to the expected schema. Responses are consistently structured, and appropriate status codes 
are returned based on the outcome of each request. Authentication and authorization mechanisms are applied to restrict 
access to sensitive routes. Together, these endpoints form the public API surface of the application.

The `routers` directory contains the following routers and their helper utilities:
- admin_panel
- discovery
- ola_hd
- oton
- user
- workflow
- workspace

Each router is dedicated to implementing only the endpoints relevant to its specific category, promoting clearer 
separation of concerns and simplifying maintenance. This modular design makes the codebase easier to navigate and reduces 
coupling between unrelated parts of the API. It also allows developers to work on specific functional areas without 
affecting other parts of the application. As a result, updates, testing, and debugging can be performed more efficiently, 
and the application structure remains scalable as new features are added.

Note: 

#### 6.1.4. Response models
In Python's FastAPI framework, response models are a helpful feature used to define and structure the data returned from 
API endpoints. By leveraging `Pydantic` models, FastAPI ensures that responses adhere to a specified schema, enhancing 
both validation and documentation. These models help in automatically generating OpenAPI documentation and allow 
developers to control which fields are included in the response, even supporting features like field aliasing, optional 
fields, and nested data. This improves the reliability and clarity of API responses.

The `models` directory contains the following response models:
- base
- discovery
- user
- workflow
- workspace

Response models are defined and structured based on the data schemas required by each router endpoint's functionality 
and expected output.

### 6.2. Operandi Broker
The Operandi broker consists of two main agent types: the `broker` and the `workers`. 

#### 6.2.1. Broker
The broker is primarily responsible for orchestrating the lifecycle of workers, including their creation, monitoring, 
and graceful termination. It utilizes Python's `psutil` library to manage and inspect worker processes, and the `signal` 
module to coordinate communication through UNIX signals, enabling an event-driven and decoupled control mechanism.

#### 6.2.2. Workers
Workers are organized into three distinct categories, with a base worker class designed to reduce code duplication across 
similar methods. Each worker listens for requests on its assigned RabbitMQ queue, consumes messages as they arrive, and 
triggers the appropriate message handler to process the request. The `submit` worker handles the submission of HPC batch 
jobs, the `status` worker monitors and updates job statuses, and the `download` worker retrieves results from the HPC 
environment upon successful job completion. 

When a termination signal is received from the broker, each worker sends a negative acknowledgment for the message it is 
currently processing to the RabbitMQ server, ensuring that no requests are lost during the module shutdown. This is 
especially crucial for the `submit` and `download` workers, as message loss could result in `job submission` or `result 
retrieval` failures. In contrast, the `status` worker can tolerate message loss with minimal impact, as its main function 
is to check and update job statuses. Additionally, users typically query the job status multiple times throughout the 
workflow job duration, which mitigates the risk of losing a few status messages.

### 6.3. Operandi Harvester

### 6.4. Operandi Client

### 6.5. Operandi Utils
#### 6.5.1. RabbitMQ
#### 6.5.2. MongoDB
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