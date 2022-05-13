import os.path
import time
import shutil

from src.priority_queue.consumer import Consumer
from src.service_broker.ssh_communication import SSHCommunication

from constants import (
    SERVICE_BROKER_IP as IP,
    SERVICE_BROKER_PORT as PORT,
)


class ServiceBroker:
    def __init__(self, host=IP, port=PORT):
        print(f"ServiceBroker Constructor: {host}:{port}")
        self.host = host
        self.port = port
        self.consumer = Consumer()
        self.ssh = SSHCommunication()

    def __del__(self):
        print(f"ServiceBroker Destructor")

    # Packs together the following:
    # a batch script,
    # a nextflow configuration,
    # a nextflow script
    # an ocrd-workspace/a mets file
    def prepare_combination(self, folder_name):
        if not os.path.exists(folder_name):
            os.makedirs(f"{folder_name}/bin", exist_ok=True)

        if os.path.exists("./batch_scripts/base_script.sh"):
            shutil.copy2("./batch_scripts/base_script.sh",
                         f"{folder_name}/")

        if os.path.exists("./nextflow/configs/nextflow.config"):
            shutil.copy2("./nextflow/configs/nextflow.config",
                         f"{folder_name}/bin/")

        if os.path.exists("./nextflow/scripts/seq_ocrd_wf_single_processor.nf"):
            shutil.copy2("./nextflow/scripts/seq_ocrd_wf_single_processor.nf",
                         f"{folder_name}/bin/")

        if os.path.exists("./workspaces/ocrd-workspace"):
            shutil.copytree("./workspaces/ocrd-workspace",
                            f"{folder_name}/bin/ocrd-workspace/", dirs_exist_ok=True)


def callback(ch, method, properties, body):
    # print(f"INFO: ch: {ch}")
    # print(f"INFO: method: {method}")
    # print(f"INFO: properties: {properties}")
    print(f"INFO: A METS URI has been consumed: {body}")


# TODO: Implement the entire service broker properly

service_broker = ServiceBroker()
service_broker.prepare_combination("test1")
service_broker.ssh.put_directory(source="test1",
                                 destination="/home/users/mmustaf/",
                                 recursive=True)

# Bash reads shell setup files, such as /etc/profile and bashrc, only if you log in interactively.
# That's where the setup of the paths and modules happen.
# You can bypass that by forcing bash to start a login shell:
# $ ssh gwdu101.gwdg.de  "bash -lc 'srun --version'"
ssh_command = "bash -lc 'sbatch /home/users/mmustaf/test1/base_script.sh'"
output, err, return_code = service_broker.ssh.execute_blocking(ssh_command)
print(f"RC:{return_code}, ERR:{err}, O:{output}")

# To consume continuously
# service_broker.consumer.set_callback(callback)
# service_broker.consumer.start_consuming()

print(f"INFO: Waiting for messages. To exit press CTRL+C.")
# Loops till there is a message inside the queue
while True:
    received = service_broker.consumer.single_consume()
    if received is not None:
        print(f"Received: {received}")
        # Do anything with the received message here

    time.sleep(2)

# Do something with the received message body
