# OPERANDI_TestRepo
This is the OPERANDI project's test repository.
CI/CD is working properly.

## 1. Introduction
TODO: To be added

This is still a draft Readme file and is under construction.

## 2. Accessing the development VM of OPERANDI
This step is only for internal developers of OPERANDI.
For installation from the source continue with the next step.

1. Create an SSH key pair (if not already done)
```sh
ssh-keygen -t rsa -b 2048 -f keyPath
```

2. Write me an e-mail with your public key attached (if not already done)

I will add your public key and provide you access to the VM.

3. Connect to our development VM (cloud@141.5.105.17) via ssh:
```sh
ssh cloud@141.5.105.17 -i keyPath
```

All installations and configurations are already done inside the VM.

You can proceed to step 4: `Executing one full cycle of OPERANDI`

## 3. Installation of OPERANDI from source
#### 1. Clone the repository and enter its directory.
```sh
git clone https://github.com/MehmedGIT/OPERANDI_TestRepo
cd OPERANDI_TestRepo
```

#### 2. Create a virtual Python environment and activate it.
```sh
python3 -m venv $HOME/venv-operandi
source $HOME/venv-operandi/bin/activate
```

#### 3. Install the RabbitMQ Server (priority queue)

3.1 First setup the repository with a single liner script:
```sh
sudo ./src/priority_queue/repo_setup.deb.sh
```

3.2 Install RabbitMQ:

Easy install:

```sh
sudo ./src/priority_queue/install.sh
```

This script should install the RabbitMQ Server properly in most cases.
`NOTE`: Always check the content of scripts before execution! 

Advanced install:

It is highly recommended to perform the steps of the `install.sh` script manually step by step.

#### 4. Install the modules of OPERANDI.
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

RabbitMQ should be running on ports 5672 and 25672. Example output of the previous command:
```sh
beam.smp    926        rabbitmq   18u  IPv4  42412      0t0  TCP *:25672 (LISTEN)
beam.smp    926        rabbitmq   33u  IPv6  42450      0t0  TCP *:5672 (LISTEN)
```

If running, go to step 4. If not running, enable and start it:
```sh
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
```

4. Open 3 new terminals and activate `venv-operandi` in all of them.
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
operandi-broker broker start --limit 1
```

For the demo run, we want to take only one request from the priority queue, thus, we limit the number of requests to be processed with the `--limit` option.

Example Service Broker output:
```sh
Service broker host:localhost port:27072
Consumer initiated
SSH connection successful
Service broker started with limit:1
INFO: Waiting for messages. To exit press CTRL+C.
```

WARNING for internal developers of OPERANDI: Currently, the development VM has no access to the HPC environment and the Service Broker cannot perform SSH connection and timeouts. Access has already been requested. Soon this problem will be solved.

7. In the third terminal start the Harvester
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

8. Results

Produced extra output on the OPERANDI Server Terminal:
```sh
INFO:     127.0.0.1:56564 - "POST /vd18_ids/?vd18_id=PPN767935306&vd18_url=https://gdz.sub.uni-goettingen.de/mets/PPN767935306.mets.xml HTTP/1.1" 200 OK
```

Produced extra output on the Service Broker Terminal:
```sh
URL: https://gdz.sub.uni-goettingen.de/mets/PPN767935306.mets.xml
Workspace Name: PPN767935306
[################################] 820/820 - 00:00:00
Submitting files is commented out!
```

Currently, the submission of files to the HPC environment is deactivated.
The line that does that is commented out. If you still want to test that have a look inside the `service_broker.py`.

## 5. Solutions to commonly occurring problems

This section provides solutions for potential problems that may arise.

TODO: To be extended as errors occur
