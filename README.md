# OPERANDI_TestRepo
This is the OPERANDI project's repository. The Readme file is still a draft and under construction.

## 1. Introduction
OPERANDI is one of the implementation projects funded by the DFG initiative OCR-D. The main goal of OCR-D is the conceptual and technical preparation of the full-text transformation of the 16th to 18th-century prints published in the German language area. The task of automatic full-text recognition is broken down into individual process steps, which can be reproduced in the open source OCR-D software. This makes it possible to create optimal workflows for the prints to be processed, and thus generate scientifically usable full texts.

The goal of OPERANDI is to develop and build an OCR-D-based implementation package for mass full-text capture with improved throughput, while improving the quality of the results. At the same time, the goal is that the implementation package can also be used by other projects and institutions with comparable requirements. Two scenarios were identified during the pilot. In the first scenario, OCR generation is to take place for works that have already been digitized, resulting in mass full-text capture. In the second scenario, OCR generation for new works to be digitized will take place as part of the digitization process.

## 2. Accessing the development VM of OPERANDI
UP-TO-DATE

This step is only for internal developers of OPERANDI.
For installation from the source continue with the next step.

1. Create an SSH key pair (if not already done)
```sh
ssh-keygen -t rsa -b 2048 -f keyPath
```

2. Write me an e-mail with your public key attached (if not already done)

I will add your public key and provide you access to the VM.

3. Connect to our development VM (cloud@141.5.99.32) via ssh:
```sh
ssh cloud@141.5.99.32 -i keyPath
```

All installations and configurations are already done inside the VM.

You can proceed to step 4: `Executing one full cycle of OPERANDI`

## 3. Installation of OPERANDI from source
#### 1. Clone the repository and enter its directory.
```sh
git clone https://github.com/MehmedGIT/OPERANDI_TestRepo
cd OPERANDI_TestRepo
```

#### 2. Install dependencies
```sh
sudo apt-get update
sudo apt-get -y install make
make deps-ubuntu
```

#### 3. Create a virtual Python environment and activate it.
```sh
python3 -m venv $HOME/venv-operandi
source $HOME/venv-operandi/bin/activate
```

#### 4. Install the RabbitMQ Server (priority queue)

3.1 First set up the repository with a single liner script:
```sh
sudo ./src/priority_queue/local_install/repo_setup.deb.sh
```

3.2 Install RabbitMQ:

Easy installation:

```sh
sudo ./src/priority_queue/local_install/install.sh
```

This script should install the RabbitMQ Server properly in most cases (on ubuntu/debian linux OS).
`NOTE`: Always check the content of scripts before execution! 

Advanced install:

It is highly recommended to perform the steps of the `install.sh` script manually step by step.

#### 5. Install the modules of OPERANDI.
```sh
make install
```

After a successful installation three executables are produced:
- operandi-server
- operandi-broker
- operandi-harvester

## 4. Executing one full cycle of OPERANDI

1. Getting credentials (if not already done)

1.1 For an account activation: Follow the instructions provided [here](https://docs.gwdg.de/doku.php?id=en:services:application_services:high_performance_computing:account_activation)

1.2 Creating a key pair for the HPC environment: Follow the instructions provided [here](https://docs.gwdg.de/doku.php?id=en:services:application_services:high_performance_computing:connect_with_ssh)

Make sure you have access to the GWDG's HPC environment from your local machine.

2. Configurations:

2.1 Set the HPC related credentials `HPC_USERNAME` and `HPC_KEY_PATH` inside:
[constants.py](./src/service_broker/service_broker/constants.py) of Service Broker.

2.2 Reinstall the OPERANDI modules to save the changes of the previous step
```sh
make install-dev
```

3. Enable and start the RabbitMQ Server (if not already running)

Check if RabbitMQ is running:
```sh
sudo lsof -i -P -n | grep LISTEN
```

RabbitMQ should be running on ports 5672, 15672, and 25672. Example output of the previous command:
```sh
beam.smp  103720  rabbitmq  18u  IPv4  383150  0t0  TCP *:25672 (LISTEN)
beam.smp  103720  rabbitmq  33u  IPv6  373659  0t0  TCP *:5672 (LISTEN)
beam.smp  103720  rabbitmq  34u  IPv4  393881  0t0  TCP *:15672 (LISTEN)
```

If running, go to step 4. If not running, enable and start it:
```sh
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
sudo rabbitmq-plugins enable rabbitmq_management
```

4. Open 2 new terminals and activate `venv-operandi` in all of them.
```sh
source $HOME/venv-operandi/bin/activate
```

5. In the first terminal start the OPERANDI Server

```sh
operandi-server server start
```

Example OPERANDI Server output:
```sh
INFO:     Started server process [34531]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
```

6. In the second terminal start the Service Broker

```sh
operandi-broker broker start
```

Example Service Broker output:
```sh
Service broker host:localhost port:27072
Consumer initiated
SSH connection successful
INFO: Waiting for messages. To exit press CTRL+C.
```

If you do not have the HPC credentials for the SSH connection, then run the mockup broker for a local execution.
Inside the development VM the ocrd/all:maximum docker image and Nextflow are already available.
```sh
operandi-broker broker start -m True
```
 
However, if you want to run the broker mockup locally on your machine you have to get the ocrd docker image and install Nextflow before starting the mockup.
```sh
docker pull ocrd/all:maximum
``` 

Check the Nextflow installation guide [here](https://www.nextflow.io/docs/latest/getstarted.html).  

7. In the third terminal start the Harvester

NOTE: Skip step 7. Go to step 8. The harvester module is not up-to-date. The location of the harvester will change.
The harvester will no longer talk to the Operandi server. Instead, there will be a direct communication 
between the Harvester and the Service broker module over the RabbitMQ.

```sh
operandi-harvester harvest start --limit 1
```

For the demo run, we want to post only one request to the OPERANDI Server, thus, we limit the number of requests to be posted with the `--limit` option.

Example Harvester output:
```sh
Harvesting started with limit:1
INFO: Starting harvesting...

INFO: Mets URL will be submitted every 10 seconds.
INFO: Posted successfully... PPN767935306
```

8. Create a request and get the results

8.1. Submit a `mets_url` and provide a `workspace_id`. 

A timestamp is added as a suffix to the provided `workspace_id`. The format of the timestamp is `_%Y%m%d_%H%M`. E.g., `2022-07-28 17:00` will become `_20220728_1700` as a suffix.

Open a new terminal and submit your mets_url. Here is an example curl request:
```sh
curl -X 'POST' \
  'http://localhost:8000/mets_url/?mets_url=https%3A%2F%2Fcontent.staatsbibliothek-berlin.de%2Fdc%2FPPN631277528.mets.xml&workspace_id=PPN631277528' \
  -H 'accept: application/json' \
  -d ''
```
Replace `mets_url=VALUE` and `workspace_id=VALUE` appropriately for your input. 
Once you submit the `mets_url` and the `workspace_id`, the service broker creates a directory named `workspace_id_%Y%m%d_%H%M`, 
downloads the mets file, and the images of fileGrp `DEFAULT` inside the mets file.
Then the broker triggers a nextflow workflow on that workspace using the base nextflow script inside the service broker
(the base nextflow script runs only the binarization processor). 
Soon, we will support a way to provide the desired `fileGrp` to be used. 
Moreover, we will offer several ready to run Nextflow scripts to choose from instead of running just the base Nextflow script.
In addition, there will be a way to provide an OCR-D process workflow textfile which will be converted to a Nextflow script.
Check [here](https://github.com/MehmedGIT/OtoN_Converter) for additional information on the OtoN (OCR-D to Nextflow) converter. 

8.2. List available workspaces. 

It shows all `workspace_id`'s currently available on the Operandi Server.

E.g.:
```sh
curl -X 'GET' \
  'http://localhost:8000/workspaces/' \
  -H 'accept: application/json'
```

8.3. Get the results

Download the zip of a `workspace_id_timestamp`. Suggestion: first list the available `workspace_id`'s to find your 
`workspace_id` with the timestamp suffix. Then replace `workspace_id=VALUE` appropriately.
Set the output path of the zip appropriately, i.e., the download location of the zip.

E.g.:
```sh
curl -X 'GET' \
  'http://localhost:8000/workspaces/workspace_id?workspace_id=PPN631277528_20220728_1700' \
  -H 'accept: application/json' --output /operandi_results/PPN631277528.zip
```

The zip file includes the following:
1. A `bin` directory with the `ocrd-workspace` and the executed base nextflow script.
2. A `work` directory that has detailed information on the processes executed with Nextflow (logs, outputs, errors etc.). 
This is especially useful for debugging!
3. A Nextflow report with execution details such as execution duration and used resources: `report.html` 
4. An `output.txt` that holds the `stdout` of the current Nextflow execution.

## 5. Solutions to commonly occurring problems

This section provides solutions for potential problems that may arise.

1. Are there any authentication errors with the SSH connection when starting the Service Broker module?

A potential reason for that error could be that your private key was not added to the SSH Agent.

Solution:
```sh
eval `ssh-agent -s`
ssh-add ~/.ssh/gwdg-cluster
```

The first command activates the SSH Agent (in case it is not active).

The second command adds the private key to the SSH Agent. 
The given path for the private key is the path inside the development VM. 
Make sure to provide the correct path for your local installation.

2. Downloading images based on mets file fails with an HTTP request exception inside the HPC environment.

This is a known problem. This happens with the mets files coming from GDZ and has nothing to the with the Operandi project itself. 
The URLs to the images inside the mets file sometimes trigger exception. 

`Exception: HTTP request failed: URL (HTTP 500)`

- Bad solution:

Manually replace `http://gdz-srv1.` with `https://gdz.` inside the mets file.

- Better solution:

For now just provide a METS file URL link from another library.

Follow these steps:

1. Start the Operandi Server (check above for instructions)
2. Start the Service Broker (check above for instructions)
3. Instead of starting the Harvester, execute the following curl command to create a request
```
curl -X 'POST' \
  'http://localhost:8000/mets_url/?mets_url=https%3A%2F%2Fcontent.staatsbibliothek-berlin.de%2Fdc%2FPPN631277528.mets.xml&mets_id=PPN631277528' \
  -H 'accept: application/json' \
  -d ''
```

The request sends the URL of a mets file of a workspace and the ID of that mets file. 

To obtain results faster we use a small workspace with just 29 pages.

4. You will receive a Job-ID back as a response. Currently, this is the ID of the job running inside the HPC cluster. This will change in the future.
