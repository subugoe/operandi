import os
import datetime
from shutil import make_archive
from fastapi import FastAPI
from fastapi.responses import FileResponse
from priority_queue.producer import Producer
from priority_queue.constants import (
    RABBIT_MQ_HOST as RMQ_HOST,
    RABBIT_MQ_PORT as RMQ_PORT
)
from .constants import (
    SERVER_HOST as HOST,
    SERVER_PORT as PORT,
    SERVER_PATH,
    PRESERVE_REQUESTS,
    OPERANDI_DATA_PATH
)


class OperandiServer:
    def __init__(self, host=HOST, port=PORT, rabbit_mq_host=RMQ_HOST, rabbit_mq_port=RMQ_PORT):

        self.host = host
        self.port = port
        self.server_path = SERVER_PATH
        self.preserve_requests = PRESERVE_REQUESTS
        self._data_path = OPERANDI_DATA_PATH

        self.vd18_id_dict = {}
        self.app = self.__initiate_fast_api_app()
        self.producer = self.__initiate_producer(rabbit_mq_host, rabbit_mq_port)

        # On startup reads the dictionary of IDs that were previously submitted
        # If PRESERVE_REQUESTS is True
        @self.app.on_event("startup")
        async def startup_event():
            if not self.preserve_requests:
                return
            if os.path.exists("vd18_ids.txt") and os.path.isfile("vd18_ids.txt"):
                with open("vd18_ids.txt", mode="r") as backup_doc:
                    for line in backup_doc:
                        line = line.strip('\n')
                        key, value = line.split(',')
                        self.vd18_id_dict[key] = value

        # On shutdown writes the dictionary of IDs to a text file
        # If PRESERVE_REQUESTS is True
        @self.app.on_event("shutdown")
        def shutdown_event():
            if not self.preserve_requests:
                return
            if len(self.vd18_id_dict):
                with open("vd18_ids.txt", mode="w") as backup_doc:
                    for k in self.vd18_id_dict:
                        backup_doc.write(f"{k}, {self.vd18_id_dict[k]}\n")

        @self.app.get("/")
        async def home():
            message = "The home page of OPERANDI server"
            _time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            json_message = {
                "message": message,
                "time": _time
            }
            return json_message

        # Used to accept Mets URLs from the user
        @self.app.post("/mets_url/")
        async def post_mets_url(mets_url: str, workspace_id: str):
            # Create a timestamp
            timestamp = datetime.datetime.now().strftime("_%Y%m%d_%H%M")
            # Append the timestamp at the end of the provided workspace_id
            workspace_id += timestamp
            publish_message = f"{mets_url},{workspace_id}".encode('utf8')

            # Send the posted mets_url to the priority queue (RabbitMQ)
            self.producer.publish_mets_url(body=publish_message)

            message = f"Mets URL posted successfully!"
            json_message = {
                "message": message,
                "mets_url": mets_url,
                "workspace_id": workspace_id
            }
            return json_message

        # List available workspaces
        @self.app.get("/workspaces/")
        async def get_workspaces():
            # TODO: Provide more appropriate way for paths
            local_workspace_path = f"{self._data_path}/ws_local"
            # For the Alpha release only mockup is used, so no hpc workspace checked
            # hpc_workspace_path = f"{self._data_path}/ws_hpc"

            workspaces = []
            for filename in os.listdir(local_workspace_path):
                workspace = os.path.join(local_workspace_path, filename)
                if os.path.isdir(workspace):
                    workspaces.append(filename)

            json_message = {
                "workspaces": workspaces
            }
            return json_message

        # Download workspace
        @self.app.get("/workspaces/workspace_id")
        async def get_workspaces(workspace_id: str):
            # TODO: Provide more appropriate way for paths
            local_workspace_path = f"{self._data_path}/ws_local"
            workspace_path = f"{local_workspace_path}/{workspace_id}"
            # For the Alpha release only mockup is used, so no hpc workspace checked
            # hpc_workspace_path = f"{self._data_path}/ws_hpc"

            if os.path.exists(workspace_path) and \
                    os.path.isdir(workspace_path):
                make_archive(workspace_path, "zip", workspace_path)
                return FileResponse(path=f"{workspace_path}.zip",
                                    media_type='application/zip',
                                    filename=f"{workspace_id}.zip")
            else:
                message = f"workspace with id: {workspace_id} was not found!"
                json_message = {
                    "message": message
                }
                return json_message

    def __initiate_fast_api_app(self):
        app = FastAPI(
            title="OPERANDI Server",
            description="REST API of the OPERANDI",
            license={
                "name": "Apache 2.0",
                "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
            },
            version="1.0.0",
            servers=[{
                "url": self.server_path,
                "description": "The URL of the OPERANDI server.",
            }],
        )
        return app

    @staticmethod
    def __initiate_producer(rabbit_mq_host, rabbit_mq_port):
        producer = Producer(
            username="operandi-server",
            password="operandi-server",
            rabbit_mq_host=rabbit_mq_host,
            rabbit_mq_port=rabbit_mq_port
        )
        print("Producer initiated")
        return producer
