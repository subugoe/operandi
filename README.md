# OPERANDI
This is the OPERANDI project's repository. The Readme file is still a draft and under construction.
The file may be slightly outdated. Will be updated after integrating the OCR-D WebApi.

## 1. Introduction
OPERANDI is one of the implementation projects funded by the DFG initiative OCR-D. The main goal of OCR-D is the 
conceptual and technical preparation of the full-text transformation of the 16th to 18th-century prints published in 
the German language area. The task of automatic full-text recognition is broken down into individual process steps, 
which can be reproduced in the open-source OCR-D software. This makes it possible to create optimal workflows for 
the prints to be processed, and thus generate scientifically usable full texts.

The goal of OPERANDI is to develop and build an OCR-D-based implementation package for mass full-text capture with 
improved throughput while improving the quality of the results. At the same time, the goal is that the implementation 
package can also be used by other projects and institutions with comparable requirements. Two scenarios were identified 
during the pilot. In the first scenario, OCR generation is to take place for works that have already been digitized, 
resulting in mass full-text capture. In the second scenario, OCR generation for new works to be digitized will take 
place as part of the digitization process.

## 2. Architecture
<picture>
  <img src="https://raw.githubusercontent.com/subugoe/operandi/main/OPERANDI_arch.png">
</picture>

### Module details:
#### 2.1. MongoDB:
Different resources such as `workspaces`, `workflows`, and `workflow jobs` are stored in the database under 
[unique resource IDs](https://en.wikipedia.org/wiki/Universally_unique_identifier): `workspace_id`, `workflow_id`, 
and `workflow_job_id`, respectively. That ID is used for faster accessing/searching for the resources and their 
metadata. The resource ID is also useful as a persistent identifier since the path of the resource itself may change 
over time.

#### 2.2. RabbitMQ Server:
The message exchange broker (server) between `Operandi Server` and `Operandi Broker`. The Operandi Server is the 
publisher and the workers of the Operandi Broker are the consumers. Depending on the coming request to the Operandi 
Server, the server forwards the requests to one of the 3 queues. On the other side, the Operandi Broker creates workers 
to consume messages from the queues to process them. Currently, there are 3 message queues available:
- for user workflow job requests (currently, there is no prioritization among users based on their type)
- for harvester workflow job requests
- for job status checks

#### 2.3. Operandi Server:
Provides various endpoints that can be used to obtain information about different resources. 
Using the endpoints the users can create, delete, get, or update resources.
The provided endpoints are respecting the proposed 
[OCR-D Web API](https://app.swaggerhub.com/apis/kba/ocr-d_web_api/0.0.1) endpoints.  
The `processing` endpoint is not utilized since Operandi concentrates mainly on running entire OCR-D workflows instead 
of single steps. However, the user could still create a workflow that has a single OCR-D processor step and execute it.

<details>
<summary> Resource types </summary>

- `Users` - used to store user related metadata. The unique identifier is the e-mail address of each user.
- `Workspaces` - each workspace must contain a [METS file](https://ocr-d.de/en/spec/mets), has at least 1 file group, and 
some images belonging to that file group. The input/output type of workspaces when interacting with the server is in 
the [OCRD-ZIP](https://ocr-d.de/en/spec/ocrd_zip) format used by our OCR-D community.
- `Workflows` - each workflow is a [Nextflow](https://www.nextflow.io/docs/latest/script.html) script. 
The input/output type of the workflows when interacting with the server is the Nextflow scripting language.
- `Workflow Jobs` - a combination of a `Workspace` and a `Workflow` resource. The specified Workflow resource is 
executed on the specified Workspace resource. Each workflow job resource contains metadata about the execution of 
the workflow such as logs of each step and reports with resource (CPU, RAM, etc.) usage. 
Each workflow job status can be queried to get the job's current state.
</details>

<details>
<summary> Endpoint interactions </summary>

The Operandi Server is responsible for accepting requests related to `users`, `workspaces`, `workflows`, and 
`workflow job` resources. In case of a `workflow job` request, the server pushes the request to one of the RabbitMQ 
queues for further delegation to the HPC environment.

A user (i.e., client) would usually send requests in the following order:
1. The user registers using the endpoint and contacts the Operandi team to get their account verified and approved. 
Once the account is approved, the user can access and use all other Operandi endpoints.
2. The user uploads a workspace of images in the [OCRD-ZIP](https://ocr-d.de/en/spec/ocrd_zip) and receives a 
unique `workspace_id` as a response.
3. The user uploads a Nextflow script and receives a unique `workflow_id` as a response.
4. The user starts a workflow job by specifying which workflow (i.e., `workflow_id`) should be executed on which 
workspace (i.e., `workspace_id`). The user should also mention which file group of images should be used as an entry 
point to the workflow. The default file group is `DEFAULT`. The response is a unique `workflow_job_id`.
5. The user polls the workflow job status using the `workflow_job_id` (till it fails or succeeds).
6. The user downloads the workspace results as an [OCRD-ZIP](https://ocr-d.de/en/spec/ocrd_zip) using the 
`workspace_id`.
7. The user downloads the workflow job execution metadata as a zip using the `workflow_job_id`.
</details>

#### 2.4. Operandi Service Broker:
The mediator between the `Operandi Server` and the `HPC environment`. The Operandi Broker is 
responsible for the creation and management of workers. A separate worker is created for each of the RabbitMQ queues.
Then each worker configures a connection and starts listening for messages coming from their respective queue. 
There are 2 types of workers. 

<details>
<summary> Type 1 </summary>

Workers for creating a slurm workspaces, transferring the workspace to the HPC environment, and triggering a slurm 
job on the transferred slurm workspace. (`W1` and `W2` on the architecture diagram). When a Type 1 worker consumes 
a message from the queue the following happens:
1. A slurm workspace zip containing a batch script, an ocrd workspace, and a Nextflow workflow is created. 
The workspace and workflow are identified again based on their `workspace_id` and `workflow_id`, respectively.
The [batch script](https://github.com/subugoe/operandi/blob/main/src/utils/operandi_utils/hpc/batch_scripts/submit_workflow_job.sh) 
contains instructions to be submitted to the HPC slurm scheduler. Some of #SBATCH directives are dynamically passed 
by the worker.
2. The slurm workspace is transferred to the HPC environment
3. A slurm job is started inside the HPC environment with the batch script.
4. The worker is not blocking till the workflow job finishes execution.
</details>

<details>
<summary> Type 2 </summary>

Workers for checking slurm job statuses in the HPC environment and transferring the results back from the HPC 
environment. (`W3` on the architecture diagram). When a Type 2 worker consumes a message from the queue the 
following happens:
1. Checks the slurm job state of the workflow job (these two are different things)
2. If there is a state change, changes the state of the workflow job in the database
3. If the state is `success` pulls the results from the HPC.
</details>

The introduction of Type 2 worker was required to avoid the blocking of the Type 1 worker 
till a slurm job finishes. Simple approach with a timeout for the Type 1 worker was not reliable enough since a slurm 
job duration may take up to 48 hours and still be successful.

#### 2.5. Operandi Harvester:
The harvesting module which automatizes the data processing in the following order: 

1. Uploads a workspace (either mets URL or ocrd workspace zip) - receives a `workspace_id`
2. uploading a workflow (Nextflow script) - receives a `workflow_id`. 
Of course, this step can be skipped if the workflow to be used is already available on the Operandi Server 
and can be referenced with some `workflow_id`
3. starting a workflow job - receives a `workflow_job_id`
4. polling the workflow job status by using the `workflow_job_id`
5. downloading the workspace output results (ocrd-zip) using the `workspace_id`
6. downloading the workflow job output results (zip) using the `workflow_job_id`

#### 2.6 GWDG HPC:
File systems - there are different file systems available in the GWDG HPC (check 
[here](https://docs.gwdg.de/doku.php?id=en:services:application_services:high_performance_computing:file_systems)), 
but Operandi uses only two: `home` and `scratch1`. Currently, the `home` directory is not utilized and is planned to be 
used for backing up failed executions that require manual investigation.

<details>
<summary> Uploading to HPC </summary>

- to the user `home` directory first and then moved to the `scratch1` file system. This step is needed when the 
transfer happens through the globally accessible transfer host of GWDG.
- to the `scratch1`. This is the more efficient approach since that file system has higher transfer rates and no 
additional transfer happens through the user `home` directory. However, the transfer host for the `scratch1` file 
system is only accessible from GÖNET, i.e., an additional proxy jump is required to connect to the GÖNET first.

Uploading with SCP: 
```shell
scp -rp LOCAL_FILE_PATH USER@transfer.gwdg.de:HPC_FILE_PATH
```

Uploading with RSYNC:
```shell
rsync -avvH LOCAL_FILE_PATH USER@transfer-scc.gwdg.de:HPC_FILE_PATH
```
</details>

<details>
<summary> Downloading from HPC </summary>

- from the user `home` - again just through the globally accessible transfer host.
- From the `scratch1` - an additional proxy jump through GÖNET is required.

Downloading with SCP: 
```shell
scp -rp USER@transfer.gwdg.de:HPC_FILE_PATH LOCAL_FILE_PATH
```

Downloading with RSYNC:
```shell
rsync -avvH USER@transfer-scc.gwdg.de:HPC_FILE_PATH LOCAL_FILE_PATH 
```
</details>

The transfer in Operandi happens directly to and from the `scratch1` file system. For that purpose, a proxy jump 
through `login.gwdg.de` is utilized. The authentication used on the proxy happens with the same key pair used for the 
HPC cluster. So, no additional key pair is required. In order to boost the transfer rates further, all files that 
belong to a single slurm workspace are uploaded and downloaded as a single zip file.

## 3. Deployment of modules
### 3.1 Prerequisites
1. Docker Engine - check the official documentation [here](https://docs.docker.com/engine/install/). 

<details>
<summary> 2. GWDG account and HPC access </summary>

In order to use the HPC environment, a GWDG account with GWDG HPC access is required. That account will be used as 
an Operandi admin account inside the HPC environment when you deploy your own instance. The admin user account is 
important because all data that is processed inside the HPC are either stored under the home directory or the 
scratch directory linked to that specific admin account.

Follow these steps:
- Get a GWDG account, check 
[here](https://docs.gwdg.de/doku.php?id=en:services:application_services:high_performance_computing:account_activation).
- Create an SSH key pair and add it to your account, check 
[here](https://docs.gwdg.de/doku.php?id=en:services:application_services:high_performance_computing:connect_with_ssh).
- Make sure you have access to the HPC environment before proceeding ahead
</details>

<details>
<summary> 3. Convert OCR-D all maximum software</summary>

This is the ocr-d all docker image of the OCR-D processors. Since running docker containers is not allowed inside the 
HPC due to security concerns, a singularity container wrapper is required. To do so, the `ocrd_all:maximum` docker image 
shall be first converted to a Singularity Image Format (SIF). Fortunately, there is already a ready to use batch script 
inside the Operandi repository - check 
[here](https://github.com/subugoe/operandi/blob/main/src/utils/operandi_utils/hpc/batch_scripts/create_sif_ocrd_all_maximum.sh).

Follow the steps:
1. Connect to the HPC
2. Copy the script to your home directory (in HPC)
3. Execute it with SLURM - `sbatch /path/to/the/script`. That will return a slurm job id and trigger a SLURM job which 
converts the docker image to SIF.
4. The job status can then be queried with `sacct -j slurm_job_id` (replace with the correct id).
5. Wait till the job finishes. The job duration varies in the range of 30-60 minutes.

As a result, a SIF file will be created. The full path will be: `/scratch1/users/${USER}/ocrd_all_maximum_image.sif`, 
where `${USER}` is the admin account created in the previous step.
</details>

<details>
<summary> 4. Download OCR-D processor models</summary>

Some OCR-D processors require trained models - check [here](https://ocr-d.de/en/models) for more details. To make sure 
that each processor inside a Nextflow workflow description is fully functional, all models should be already available. 

Again, there is a ready to use batch script that does that - check 
[here](https://github.com/subugoe/operandi/blob/main/src/utils/operandi_utils/hpc/batch_scripts/download_all_ocrd_models.sh).
As in the previous step execute the batch script and wait for the slurm job to finish.

As a result, all models will be downloaded and available in path: `/scratch1/users/${USER}/ocrd_models`, 
where `${USER}` is the admin account.
</details>

### 3.2. Operandi configurations
<details>
<summary> 1. RabbitMQ definitions file </summary>

Used to configure users, virtual hosts, message queues, and more. It is suggested to create a single admin account to 
be used for authentication purposes. Check an example definitions file for Operandi 
[here](https://github.com/subugoe/operandi/blob/main/src/rabbitmq_definitions.json). That definition creates a user 
account `operandi_user` with password `operandi_password`, creates two virtual hosts `/` (default/root) and `test`. 
Sets permissions for `operandi_user` to access both virtual hosts. It also creates several queues per virtual host. 
The exchanges and bindings are left empty because they are defined programmatically, check 
[here](https://github.com/subugoe/operandi/tree/main/src/utils/operandi_utils/rabbitmq). For more details regarding 
the definitions check the official RabbitMQ documentation [here](https://www.rabbitmq.com/configure.html).

Warning: Do not use the already exposed credentials for your production environment. Make sure to create your own 
definitions file and set the correct path as an environment variable (coming next).

</details>

<details>
<summary> 2. Environment variables </summary>

The Operandi repository contains several environment files (`.env`, `docker.env`, `tests/.env`) that can be used after modifying the relevant fields. 
For a working environment simply replace the variables below:

```dotenv
OPERANDI_HPC_USERNAME=GWDG_USER
OPERANDI_HPC_SSH_KEYPATH=PATH_TO_HPC_SSH_KEY
```

The HPC username is your GWDG account and the ssh key is the key produced in the `Prerequisites` section above.

Warning: For the production environment make sure to properly configure all environment variables related to the 
credentials!

</details>

### 3.3. Deploy all modules in docker
After adapting the `docker.env` file, simply run:
```shell
docker compose -f ./docker-compose_image_based.yml --env-file docker.env up -d
```

There are 2 identical docker compose files. The one used in the command above downloads the prebuilt remote docker 
images of the Operandi Server and Operandi Broker. The other one, `docker-compose.ymp`, builds docker images from the 
source code. 

<details>
 <summary> Check if modules are running: </summary>

By default, the MongoDB is listening on port 27018 and the RabbitMQ server is listening on ports 5672, 15672, and 25672. 
The Operandi Server is listening on port 80. Check by either:

```sh
docker ps
```
```
CONTAINER ID   IMAGE                                  COMMAND                  CREATED          STATUS                    PORTS                                                                                                                                                                                     NAMES
694fa8b9961d   ghcr.io/subugoe/operandi-server:main   "operandi-server sta…"   15 seconds ago   Up 11 seconds             0.0.0.0:80->8000/tcp, :::80->8000/tcp                                                                                                                                                     operandi-server
73159ad43f96   ghcr.io/subugoe/operandi-broker:main   "operandi-broker sta…"   15 seconds ago   Up 11 seconds                                                                                                                                                                                                       operandi-broker
8fe666ecd451   rabbitmq:3.12-management               "docker-entrypoint.s…"   15 seconds ago   Up 14 seconds (healthy)   4369/tcp, 5671/tcp, 0.0.0.0:5672->5672/tcp, :::5672->5672/tcp, 15671/tcp, 0.0.0.0:15672->15672/tcp, :::15672->15672/tcp, 15691-15692/tcp, 0.0.0.0:25672->25672/tcp, :::25672->25672/tcp   operandi-rabbitmq
2bcdae9b19b9   mongo                                  "docker-entrypoint.s…"   15 seconds ago   Up 14 seconds (healthy)   0.0.0.0:27017->27017/tcp, :::27017->27017/tcp                                                                                                                                             operandi-mongodb

```

or

```sh
sudo lsof -i -P -n | grep LISTEN
```
```
docker-pr 19979            root    4u  IPv4 203595      0t0  TCP *:27017 (LISTEN)
docker-pr 19986            root    4u  IPv6 199569      0t0  TCP *:27017 (LISTEN)
docker-pr 19999            root    4u  IPv4 210212      0t0  TCP *:25672 (LISTEN)
docker-pr 20005            root    4u  IPv6 214698      0t0  TCP *:25672 (LISTEN)
docker-pr 20017            root    4u  IPv4 206766      0t0  TCP *:15672 (LISTEN)
docker-pr 20023            root    4u  IPv6 216148      0t0  TCP *:15672 (LISTEN)
docker-pr 20036            root    4u  IPv4 202653      0t0  TCP *:5672 (LISTEN)
docker-pr 20042            root    4u  IPv6 210254      0t0  TCP *:5672 (LISTEN)
docker-pr 20582            root    4u  IPv4 220165      0t0  TCP *:80 (LISTEN)
docker-pr 20589            root    4u  IPv6 219177      0t0  TCP *:80 (LISTEN)

```


</details>

### 3.4. Deploy modules separately

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

### 3.5. Interactive API documentation

Check the interactive API documentation of the Operandi server once there is a running server 
instance (http://localhost/docs). Operandi implements the Web API from OCR-D and extends it.

1. OCR-D WebAPI [spec](https://github.com/OCR-D/spec/blob/master/openapi.yml)
2. OCR-D WebAPI [swagger](https://app.swaggerhub.com/apis/kba/ocr-d_web_api/0.0.1#/).
3. OCR-D WebAPI [repo](https://github.com/OCR-D/ocrd-webapi-implementation).

## 4. Solutions to potential problems

This section provides solutions for potential problems that may arise.

<details>
 <summary> 1. Authentication errors using SSH .</summary>

A potential reason for that error could be that your private key was not added to the SSH Agent.

Solution:
```sh
eval `ssh-agent -s` &&
ssh-add /path/to/your_key
```

The first command activates the SSH Agent (in case it is not active).

The second command adds the private key to the SSH Agent. 
The given path for the private key is the path inside the development VM. 
Make sure to provide the correct path for your local installation.

</details>

## 5. More insights regarding Operandi, Nextflow, and GWDG HPC cluster:
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
resources when a process fails due to lack of enough resources (i.e. memory). Consider this simple example below: 
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
