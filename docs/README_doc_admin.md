# Admin Documentation
This document aims to guide administrators who want to deploy Operandi as a service.

## 1. Prerequisites

#### 1.1. Project Folder
The Operandi project needs a project folder to store the required data inside the NHR partition of GWDG HPC.
After the project is set up the [project portal](https://hpcproject.gwdg.de) can be used to check more information such 
as `project path`, `login nodes`, `project members`, and the specific `HPC user` account of each member. The application 
is usually completed by the professor assigned as a project lead.

#### 1.2. Project member account
In order to use the HPC environment, a GWDG account with GWDG HPC access is required. That member account of the 
admin will be used as an Operandi account inside the HPC environment. All processing jobs submitted by the Operandi 
Server to the HPC will be running under this account.

Note: Make sure you have access to the HPC environment before proceeding ahead.

#### 1.3. Docker Engine - check the official documentation [here](https://docs.docker.com/engine/install/)

The docker engine is required to deploy different modules of the Operandi project as docker containers. Install it.

## 2. Configurations

#### 2.1. RabbitMQ definitions file
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

#### 2.2. Environment variables
The Operandi repository contains several environment files (`.env`, `docker.env`, `tests/.env`) that can be used after 
modifying the relevant fields. Here is an example to copy-paste:

```dotenv
OPERANDI_DB_NAME=operandi_db_production
OPERANDI_DB_ROOT_USER=db_admin
OPERANDI_DB_ROOT_PASS=db_admin_pass
OPERANDI_DB_URL=mongodb://db_admin:db_admin_pass@mongo-db-host:27017
OPERANDI_HARVESTER_DEFAULT_USERNAME=harv_default
OPERANDI_HARVESTER_DEFAULT_PASSWORD=harv_default_pass
OPERANDI_HPC_SSH_KEYPATH=<HPC_PRIVKEY_PATH>
OPERANDI_HPC_PROJECT_USERNAME=<HPC_PROJECT_USERNAME>
OPERANDI_HPC_PROJECT_NAME=operandi_prod
OPERANDI_LOGS_DIR=/tmp/operandi_logs_prod
OPERANDI_RABBITMQ_CONFIG_JSON=<RABBITMQ_DEFINITIONS_FILE_PATH>
OPERANDI_RABBITMQ_URL=amqp://<RMQ_USERNAME>:<RMQ_PASSWORD>@rabbit-mq-host:5672/
OPERANDI_SERVER_BASE_DIR=/tmp/operandi_data_prod
OPERANDI_SERVER_DEFAULT_USERNAME=server_default
OPERANDI_SERVER_DEFAULT_PASSWORD=server_default_pass
OPERANDI_SERVER_URL_LIVE=http://operandi.ocr-d.de
OPERANDI_SERVER_URL_LOCAL=http://0.0.0.0:8000
OCRD_DOWNLOAD_RETRIES=10
```

Note1: The `OPERANDI_DB_URL` must contain the proper `OPERANDI_DB_ROOT_USER` and `OPERANDI_DB_ROOT_PASS`.

Note2: The `OPERANDI_RABBITMQ_URL` must contain the proper `<RMQ_USERNAME>` and `<RMQ_PASSWORD>` specified in the 
RabbitMQ definitions file created in the step 2.1.

Note3: Do not change the default ports for the DB and the RabbitMQ unless you know what you are doing. In case you 
change them make sure you adapt the docker compose files properly to reflect these changes.

Note4: Adapt the `OPERANDI_SERVER_URL_LIVE` to its actual value.

Warning: For the production environment make sure to properly configure all environment variables related to the 
credentials!

#### 2.3. Preparation of OCR-D processor SIFS

This is the OCR-D all software docker image of the OCR-D processors. Since running docker containers is not allowed 
inside the HPC due to security concerns, a Singularity container wrapper is required. To do so, the docker images shall 
be first converted to a Singularity Image Format (SIF). Fortunately, there are already ready to use batch scripts inside 
the Operandi repository.

Build the latest versions of OCR-D processor SIFS from their docker images:
- Use the `batch_create_ocrd_slim_sif_images.sh` batch script to do that as a slurm job to build slim sif images.
- Use the `batch_create_ocrd_all_maximum_sif.sh` batch script to do that as a slurm job to build a single fat sif image.

Note: Either of the two should be good. Do not forget to set the `HPC_USE_SLIM_IMAGES` constant to switch between 
the 1) the slim images and 2) the fat image.

Warning: Make sure to adapt the proper project paths inside the scripts before executing the scripts as jobs.

Follow these steps:
- 2.3.1. Connect to the HPC
- 2.3.2. Copy the script to the project home directory (in HPC)
- 2.3.3. Execute it with SLURM - `sbatch /path/to/the/script`. That will return a slurm job id and trigger a SLURM job which 
converts the docker images to SIFs.
- 2.3.4. The job status can then be queried with `sacct -j slurm_job_id` (replace with the correct id).
- 2.3.5. Wait till the job finishes. The job duration varies in the range of 30-60 minutes.

As a result, SIF files will be generated under `<HPC_PROJECT_PATH>/ocrd_processor_sifs/`

#### 2.4. Preparation of OCR-D processor models

Some OCR-D processors require trained models - check [here](https://ocr-d.de/en/models) for more details. To make sure 
that each processor inside a Nextflow workflow description is fully functional, all models should be already available.

Get the latest versions of OCR-D processor models:
- Use the `batch_download_ocrd_all_models.sh` batch script to do that as a slurm job to download all models. 
Transfer the batch script to the project folder in the HPC and execute it.

Warning: Make sure to adapt the proper project paths inside the script before executing the script as a job.

Refer to the steps in 2.3.1. - 2.3.5. above to run the script.

As a result, all registered models will be downloaded and available under `<HPC_PROJECT_PATH>/ocrd_models/`

## 3. Deployment of Operandi in a production VM

### 3.1 Configurations
Let's assume the Operandi repository is cloned under:
```
/home/cloud/repos/operandi
```

Let's assume all our production files are structured inside a `deploy` folder such as:
```
/home/cloud/deploy/rabbitmq_definitions.json
/home/cloud/deploy/operandi-production.env
/home/cloud/deploy/deploy-operandi-local-image-based.sh
/home/cloud/deploy/deploy-operandi-remote-image-based.sh
```

- `rabbitmq_definitions.json` is the file created in step 2.1
- `operandi-production.env` is the file created in step 2.2

The content of `deploy-operandi-local-image-based.sh`:
```commandline
cd /home/cloud/repos/operandi
git pull origin main
cd /home/cloud/deploy
docker compose -f /home/cloud/repos/operandi/docker-compose.yml --env-file /home/cloud/deploy/operandi-production.env down --remove-orphans
docker rmi operandi-server:latest
docker rmi operandi-broker:latest
docker compose -f /home/cloud/repos/operandi/docker-compose.yml --env-file /home/cloud/deploy/operandi-production.env up -d
```

The content of `deploy-operandi-remote-image-based.sh`:
```commandline
docker compose -f /home/cloud/repos/operandi/docker-compose_image_based.yml --env-file /home/cloud/deploy/operandi-production.env down --remove-orphans
docker rmi ghcr.io/subugoe/operandi-server:latest
docker rmi ghcr.io/subugoe/operandi-broker:latest
docker compose -f /home/cloud/repos/operandi/docker-compose_image_based.yml --env-file /home/cloud/deploy/operandi-production.env up -d
```

### 3.2 Deployment

Then simply execute either of the two scripts above, e.g:
```shell
./deploy-operandi-local-image-based.sh
```

or 

```shell
./deploy-operandi-remote-image-based.sh
```

The difference between the two scripts is that:
- the first one creates docker images from the local code. Good in cases when CI/CD fails to generate images and a fast 
local fix is required
- the second one uses the docker images generated by the CI/CD pipeline of the Operandi repository. This should be the 
preferred way to do.

### 3.3. Check if modules are running
<details>
 <summary> Click to expand </summary>

By default, the MongoDB is listening on port 27018 and the RabbitMQ server is listening on ports 5672, 15672, and 25672. 
The Operandi Server is listening on port 80. 

Check by either:
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

## 4. Logging and Monitoring
TODO:

## 5. Maintenance
TODO: 

## 6. General suggestions
TODO:

## 7. FAQ
TODO: Extend further

<details>
 <summary> 1. Authentication errors using SSH </summary>

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
