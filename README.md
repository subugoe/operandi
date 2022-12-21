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

## 3. Accessing the development VM of OPERANDI
This step is only for internal developers of OPERANDI.
For installation from the source continue with the next step. 
Connect to our development VM (cloud@141.5.99.32) via ssh:
```sh
ssh cloud@141.5.99.32 -i /path/to/your_key
```
(Currently, the dev VM is not up-to-date)

## 4. Installation of OPERANDI from source
#### 4.1. Clone the repository and enter its directory.
```sh
git clone git@github.com:subugoe/operandi.git
cd operandi
```

#### 4.2. Install dependencies
```sh
sudo apt-get update
sudo apt-get -y install make
sudo make deps-ubuntu
```

#### 4.3. Create a virtual Python environment and activate it.
```sh
python3 -m venv $HOME/venv-operandi
source $HOME/venv-operandi/bin/activate
```

#### 4.4. Install the modules of OPERANDI.
```sh
make install-dev
```

## 5. Configurations

Select either of the two options and fulfill the requirements.

#### 5.1 Option 1: The service broker executes workflows on the local host

<details>
<summary> 5.1.1 Requirements </summary>

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
 <summary> 5.1.2 Configurations </summary>
By default the service broker is configured to run locally. 
No further configurations needed.
</details>

#### 5.2 Option 2: The service broker executes workflows in the HPC environment

<details>
<summary> 5.2.1 Requirements </summary>

1. GWDG credentials, check [here](https://docs.gwdg.de/doku.php?id=en:services:application_services:high_performance_computing:account_activation).
2. Access to the HPC environment, check [here](https://docs.gwdg.de/doku.php?id=en:services:application_services:high_performance_computing:connect_with_ssh).
</details>

<details>
<summary> 5.2.2 Configurations </summary>

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

## 6. Executing one full cycle of OPERANDI

Executing steps `6.1` and `6.2` for the first time will take more time - downloading and building.

#### 6.1 Start the MongoDB docker container
```bash
make start-mongo
```

#### 6.2 Start the RabbitMQ docker container
```bash
make start-rabbitmq
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

#### 6.3 Start the Operandi broker
Depending on the configuration in `step 4`, there are two options. 
To run a service broker instance that executes workflows locally or 
an instance that executes workflows in the HPC environment. 

Open a new terminal, activate the virtual Python environment created in `step 4.3`, and 
start one of the broker instances.

<details>
 <summary> Local instance </summary>

```bash
source $HOME/venv-operandi/bin/activate
make start-broker-local 
```
</details>

<details>
 <summary> HPC instance </summary>

```bash
source $HOME/venv-operandi/bin/activate
make start-broker-hpc 
```
</details>

#### 6.4 Start the Operandi server

As in `step 6.3`, activate the environment, then start the server.
```bash
source $HOME/venv-operandi/bin/activate
make start-server
```

#### 6.5 Start the Harvester (currently, out of service, skip)
As in `step 6.3`, activate the environment, then start the harvester.
```bash
source $HOME/venv-operandi/bin/activate
make start-harvester
```
The harvesting module will harvest only a single mets url workspace by default.
It is also possible to harvest more than one mets url. 
To do so start the harvester by setting the desired limit.
Currently, there are no limit checks, so do not use a big `N` value.
```bash
operandi-harvester start --limit N
```

#### 6.6 Interactive API documentation

Check the interactive API documentation of the Operandi server once there is a running server instance (http://localhost:8000/docs).
Operandi reuses the provided API from OCR-D and extends it.

1. OCR-D WebAPI [spec](https://github.com/OCR-D/spec/blob/master/openapi.yml)
2. OCR-D WebAPI [swagger](https://app.swaggerhub.com/apis/kba/ocr-d_web_api/0.0.1#/).
3. OCR-D WebAPI [repo](https://github.com/OCR-D/ocrd-webapi-implementation).

#### 6.7 Curl requests
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

## 7. Solutions to potential problems

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
