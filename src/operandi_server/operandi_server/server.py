import os
import datetime
from shutil import make_archive

from fastapi import FastAPI
from fastapi.responses import FileResponse
from ocrd_webapi.database import initiate_database
from ocrd_webapi.routers import (
    workflow,
    workspace,
)

from priority_queue.producer import Producer
from priority_queue.constants import (
    RABBIT_MQ_HOST as RMQ_HOST,
    RABBIT_MQ_PORT as RMQ_PORT
)
from .constants import (
    SERVER_HOST as HOST,
    SERVER_PORT as PORT,
    SERVER_PATH,
    OPERANDI_DATA_PATH,
    WORKFLOWS_DIR,
    WORKSPACES_DIR,
    DB_URL,
)


class OperandiServer:
    def __init__(self, host=HOST, port=PORT, rabbit_mq_host=RMQ_HOST, rabbit_mq_port=RMQ_PORT):
        self.host = host
        self.port = port
        self.server_path = SERVER_PATH
        self._data_path = OPERANDI_DATA_PATH

        self.app = self.__initiate_fast_api_app()

        # The following lines reuse the routers from the OCR-D WebAPI
        self.app.include_router(workflow.router)
        self.app.include_router(workspace.router)
        # Don't put this out of comments yet - missing confing files/malfunctioning
        # self.app.include_router(discovery.router)
        # self.app.include_router(processor.router)

        self.producer = self.__initiate_producer(rabbit_mq_host, rabbit_mq_port)

        @self.app.on_event("startup")
        async def startup_event():
            os.makedirs(WORKSPACES_DIR, exist_ok=True)
            os.makedirs(WORKFLOWS_DIR, exist_ok=True)
            await initiate_database(DB_URL)

        @self.app.on_event("shutdown")
        def shutdown_event():
            pass

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
        @self.app.post("/mets_url", tags=["Workspace"])
        async def operandi_post_mets_url(mets_url: str, workspace_id: str):
            """
            Operandi extension to Workspace
            """
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
        @self.app.get("/workspaces")
        async def get_workspaces():
            # TODO: Provide more appropriate way for paths
            local_workspace_path = f"{WORKSPACES_DIR}/ws_local"
            # For the Alpha release only mockup is used, so no hpc workspace checked
            # hpc_workspace_path = f"{WORKSPACES_DIR}/ws_hpc"

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
            local_workspace_path = f"{WORKSPACES_DIR}/ws_local"
            workspace_path = f"{local_workspace_path}/{workspace_id}"
            # For the Alpha release only mockup is used, so no hpc workspace checked
            # hpc_workspace_path = f"{WORKSPACES_DIR}/ws_hpc"

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
            version="1.1.0",
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
