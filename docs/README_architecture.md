# Operandi Architecture
This document provides information regarding the Operandi architecture.
<picture>
  <img src="https://raw.githubusercontent.com/subugoe/operandi/main/OPERANDI_arch.png">
</picture>

## 1. Operandi Modules

### 1.1. MongoDB
Different resources such as `workspaces`, `workflows`, and `workflow jobs` are stored in the database under 
[unique resource IDs](https://en.wikipedia.org/wiki/Universally_unique_identifier): `workspace_id`, `workflow_id`, 
and `workflow_job_id`, respectively. That ID is used for faster accessing/searching for the resources and their 
metadata. The resource ID is also useful as a persistent identifier since the path of the resource itself may change 
over time.

### 1.2. RabbitMQ Server
The message exchange broker (server) between `Operandi Server` and `Operandi Broker`. Typically, the Operandi Server is the 
publisher and the workers of the Operandi Broker are the consumers. Depending on the coming request to the Operandi 
Server, the server forwards the requests to one of the queues. On the other side, the Operandi Broker creates workers 
to consume messages from the queues to process them. By default, there are the following message queues available:
- `operandi_queue_users` - for user workflow job requests (there is no prioritization among users)
- `operandi_queue_harvester` - for harvester workflow job requests (there is no prioritization among harvesters)
- `operandi_queue_job_statuses` - for job status checks
- `operandi_queue_hpc_downloads` - for hpc results download

Also check the default example `rabbitmq_definitions.json` in the repository for more details.

### 1.3. Operandi Server
TODO: Reconsider the `Resource types` field

Provides various endpoints that can be used to obtain information about different resources. 
Using the endpoints the users can create, delete, get, or update resources.
The provided endpoints are usually respecting the proposed 
[OCR-D Web API](https://app.swaggerhub.com/apis/kba/ocr-d_web_api/0.0.1) endpoints.  
The `processing` endpoint is not utilized since Operandi concentrates mainly on running entire OCR-D workflows instead 
of single steps. However, the user could still create a workflow that has a single OCR-D processor step and execute it.

Resource types:
- `Users` - used to store user related metadata. The unique identifier is the e-mail address of each user.
- `Workspaces` - each workspace must contain a [METS file](https://ocr-d.de/en/spec/mets), has at least 1 file group, 
and some images belonging to that file group. The input/output type of workspaces when interacting with the server is in 
the [OCRD-ZIP](https://ocr-d.de/en/spec/ocrd_zip) format used by the OCR-D community.
- `Workflows` - each workflow is a [Nextflow](https://www.nextflow.io/docs/latest/script.html) script. 
The input/output type of the workflows when interacting with the server is the Nextflow scripting language.
- `Workflow Jobs` - a combination of a `Workspace` and a `Workflow` resource. The specified Workflow resource is 
executed on the specified Workspace resource. Each workflow job resource contains metadata about the execution of 
the workflow such as logs of each step and reports with resource (CPU, RAM, etc.) usage. 
Each workflow job status can be queried to get the job's current state.

### 1.4. Operandi Broker
The mediator between the `Operandi Server` and the `HPC environment`. The Operandi Broker is 
responsible for the creation and management of different workers. A separate worker is created for each of the RabbitMQ 
queues. Then each worker configures a connection and starts listening for messages coming from their respective queue. 
There are 3 different types of workers:

<details>
<summary> <b>Type 1 - Submit Worker</b> </summary>

Worker for creating a slurm workspace, transferring the workspace to the HPC environment, and triggering a slurm 
job on the transferred slurm workspace. (`W1` and `W2` on the architecture diagram). When a `Type 1` worker consumes 
a message from the queue the following happens:
1. A slurm workspace zip containing an ocrd workspace, and a Nextflow workflow is created. 
The `workspace` and `workflow` are identified again based on their `workspace_id` and `workflow_id`, respectively.
A batch script located inside the HPC environment contains instructions to be submitted to the HPC slurm scheduler. 
Some of `#SBATCH` directives of that batch script are dynamically passed by the worker.
2. Sets state `TRANSFERRING_TO_HPC` to both the workspace and workflow job in the database.
3. The slurm workspace is transferred to the HPC environment
4. A slurm job is started inside the HPC environment with a batch script.

Note: The worker is no longer blocking till the workflow job finishes execution.
</details>

<details>
<summary> <b>Type 2 - Job Status Worker</b> </summary>

Worker for checking slurm job statuses in the HPC environment. (`W3` on the architecture diagram). When a `Type 2` 
worker consumes a message from the queue the following happens:
1. Checks the `slurm job state` of the workflow job in the HPC environment
2. If the `slurm job state` is different from the state read from the database: 
   1. Writes the new state to the database
3. Converts the `slurm job state` to `workflow job state`
4. If the previous `workflow job state` is one of `SUCCESS`, `FAILED`, or `TRANSFERRING_FROM_HPC`:
   1. The rest of the steps are skipped. Better to do that check to avoid duplicate entries in the download queue. 
5. If the `workflow job state` is different from the state read from the database:
   1. Writes the new state to the database
6. If the `workflow job state` is one of `HPC_SUCCESS` or `HPC_FAILED`:
   1. Writes the state of the `workspace` to `TRANSFERRING_FROM_HPC` in the database. 
   2. Writes the state of the `workflow job` to `TRANSFERRING_FROM_HPC` in the database.
7. Pushes a download message to the hpc download queue to request downloading of the results
</details>

<details>
<summary> <b>Type 3 - Job Download Worker</b> </summary>

Worker for transferring the results back from the HPC environment to the Operandi Server. (Currently, not represented in 
the architecture diagram). When a `Type 3` worker consumes a message from the queue the following happens:
1. Checks the `workflow job state` of the workflow job in the request
2. If the `workflow job state` is `HPC_SUCCESS`:
   1. Downloads `slurm job` log file.
   2. Downloads the `workspace` results.
   3. Downloads the `workflow job` logs.
   4. Sets the `workspace state` to `READY`.
   5. Sets the `workflow job state` to `SUCCESS`.
3. If the `workflow job state` is `HPC_FAILED`:
   1. Downloads `slurm job` log file.
   2. Sets the `workspace state` to `READY`.
   3. Sets the `workflow job state` to `FAILED`.
</details>

The introduction of `Type 2` worker was required to avoid the blocking of the Type 1 worker till a slurm job finishes. 
Simple approach with a timeout for the Type 1 worker was not reliable enough since a slurm job duration may take up 
to 48 hours and still be successful.

The introduction of `Type 3` worker was required to reduce the complexity of the `Type 2` worker and for better 
error handling in different scenarios.

All workers also write different usage statistics to the database to reflect amount of pages processed.

### 1.5. Operandi Client
TODO: Consider adding more details.

The Operandi client is mainly provided for the following reasons:
1. To be used internally by the Operandi Harvester module
2. To be used as a Python library by other third parties

### 1.6. Operandi Harvester
TODO: Add more information about the cycle and the VD18 JSON

The harvesting module is responsible for executing the following cycle:
1. Uploads a workspace (either mets URL or ocrd workspace zip) - receives a `workspace_id`.
2. Uploads a workflow (Nextflow script) - receives a `workflow_id`. 
Of course, this step can be skipped. If the workflow to be used is already available on the Operandi Server just using 
the `workflow_id` to reference it will suffice.
3. Starts a workflow job - receives a `workflow_job_id`
4. Polls the workflow job status by using the `workflow_job_id`
5. Downloads the workspace output results (ocrd-zip) using the `workspace_id`
6. Downloads the workflow job output results (zip) using the `workflow_job_id`

The cycle is managed by utilizing the Operandi client module.

## 2. High Performance Cluster (HPC)

The Operandi project has a project folder to store the required data inside the NHR partition of GWDG HPC.
After the project is set up the [project portal](https://hpcproject.gwdg.de) can be used to check more information such 
as `project path`, `login nodes`, `project members`, and the specific `HPC user` account of each member.

In the next subsections, brief introduction to different HPC related topics are provided. 
The last section provides links to external official documentation of the GWDG HPC for more extensive information on 
the topics.

### 2.1. Connecting to the login nodes

In order to connect to any of the Emmy Phase 2 nodes:
```shell
ssh glogin-p2.hpc.gwdg.de -l <PROJECT_USERNAME> -i <FULLPATH_OF_PRIVKEY>
```

### 2.2. Storage Systems

The Operandi project currently utilizes the SCRATCH MDC (HDD) storage (with 8.4 PiB capacity) to store different files:
- OCR-D processor images (SIF variants of the respective Docker images)
- Different models required by the OCR-D processor images
- OCR results that are stored temporarily before they are pulled by the Operandi service

Note: More detailed information about the Operandi project files can be found in hte documentation for administrators.

Note2: The HDD scratch storage is utilized instead of the SSD one due to the bigger available capacity. The SSD storage 
usually gets filled up to 90% by all active users of the HPC, hence, the more robust HDD option is preferred. 
The processing itself happens inside the local SSD storage of the computing nodes.

### 2.3 Data transfers

<details>
<summary> 2.3.1 Uploading to the HPC project folder </summary>

Uploading with RSYNC:
```shell
rsync -e 'ssh -i <FULLPATH_OF_PRIVKEY>' -avvH <LOCAL_SOURCE> <PROJECT_USERNAME>@glogin.hpc.gwdg.de:<REMOTE_TARGET>
```
</details>

<details>
<summary> 2.3.2 Downloading from the HPC project folder </summary>

Downloading with RSYNC:
```shell
rsync -e 'ssh -i <FULLPATH_OF_PRIVKEY>' -avvH <PROJECT_USERNAME>@glogin.hpc.gwdg.de:<REMOTE_SOURCE> <LOCAL_TARGET> 
```
</details>

### 2.4. Slurm Scheduler

Processing jobs are submitted to the slurm scheduler of the HPC environment. When submitting a processing job to the 
Operandi Server, the user can specify the HPC partition, amount of CPUs, and RAM. By default, all jobs are submitted to 
the `standard96:shared` partition with `4 CPUs` and `64GB RAM`. 16GB RAM per allocated CPU is the minimum ratio for 
resources to avoid out of memory errors.

Note: Using a partition with GPUs may not always be cost-efficient since not all steps in a processing job may utilize 
it efficiently. Hence, it is suggested to use single step workflows for processors that benefit from GPUs the most.

### 2.5. Computing Nodes

Only computing nodes with available local SSD are utilized to process OCR jobs. All intermediate results of running jobs 
are stored in the internal SSD storage. Previously the data of running jobs was stored in the HDD/SSD scratch storage 
which was leading to issues such as surpassing the 
[Inode limit](https://docs.hpc.gwdg.de/how_to_use/the_storage_systems/quota/index.html#inode). This is understandable 
since every job may produce more than hundreds of thousands of files.

### 2.6. Modules

This section describes all modules required by a computing node in order to run an OCR job.

#### 2.6.1. Singularity container

[Singularity](https://sylabs.io/docs/) is required for executing the external software (OCR-D processors).

#### 2.6.2. Nextflow

[Nextflow](https://www.nextflow.io/) is the orchestrator of the OCR-D processors to achieve horizontal- and 
vertical-level parallelization.

### 2.7. External documentation

More information regarding the topics discussed above can be found in the official GWDG HPC documentation: 
- the [NHR application process](https://docs.hpc.gwdg.de/start_here/nhr_application_process/index.html)
- the [user accounts](https://docs.hpc.gwdg.de/start_here/user_disambiguation/index.html)
- the [connecting SSH](https://docs.hpc.gwdg.de/start_here/connecting/index.html)
- the [storage systems](https://docs.hpc.gwdg.de/how_to_use/the_storage_systems/index.html)
- the [data transfer](https://docs.hpc.gwdg.de/how_to_use/data_transfer/index.html)
- the [slurm scheduler](https://docs.hpc.gwdg.de/how_to_use/slurm/index.html)
- the [compute partitions](https://docs.hpc.gwdg.de/how_to_use/compute_partitions/index.html)

## 3. OCR-D processors and their models

The software for the OCR process is developed by the [OCR-D](https://ocr-d.de/en/) community. This software is 
distributed as a single fat image (ocrd_all) or as many slim images. Check the official repository 
[here](https://github.com/OCR-D/ocrd_all). A brief, but incomplete description list of OCR-D processor images can be 
found [here](https://github.com/subugoe/operandi/tree/main/docs/ocrd_docker_images_info.txt).

Operandi supports both distributions and either of the solutions could be configured by the administrator.
The development and support for the single fat image will be discontinued soon. Hence, it is advised to adopt and use 
the slim image solution. Check the administrator documentation for more information.

## 4. Ola-HD (External Service)
Results obtained from Operandi are supposed to be transferred to the long term archive storage 
[Ola-HD](https://ola-hd.ocr-d.de/). The official Ola-HD repositories: [backend](https://github.com/subugoe/olahd_backend) 
and [frontend](https://github.com/subugoe/olahd_user_frontend).
