import os
import datetime
from shutil import make_archive

import logging

from fastapi import FastAPI
from fastapi.responses import FileResponse
from ocrd_webapi.database import initiate_database
from ocrd_webapi.routers import (
    discovery,
    workflow,
    workspace,
)
from ocrd_webapi.managers.workspace_manager import WorkspaceManager
from ocrd_webapi.models.workspace import WorkspaceRsrc
from ocrd_webapi.utils import bagit_from_url

from ocrd_webapi.rabbitmq import RMQPublisher
from rabbit_mq_utils.constants import (
    RABBIT_MQ_HOST as RMQ_HOST,
    RABBIT_MQ_PORT as RMQ_PORT,
    DEFAULT_EXCHANGER_NAME,
    DEFAULT_EXCHANGER_TYPE,
    DEFAULT_QUEUE_SERVER_TO_BROKER
)
from .constants import (
    SERVER_HOST as HOST,
    SERVER_PORT as PORT,
    SERVER_PATH,
    OPERANDI_DATA_PATH,
    WORKFLOWS_DIR,
    WORKSPACES_DIR,
    DB_URL,
    LOG_LEVEL,
    LOG_FORMAT
)


class OperandiServer:
    def __init__(self, host=HOST, port=PORT, rabbit_mq_host=RMQ_HOST, rabbit_mq_port=RMQ_PORT):
        self.host = host
        self.port = port
        self.server_path = SERVER_PATH
        self._data_path = OPERANDI_DATA_PATH
        self.workspace_manager = WorkspaceManager()

        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
        logging.getLogger(__name__).setLevel(LOG_LEVEL)
        self._server_logger = logger

        self._server_logger.info(f"Operandi host:{host}, port:{port}")
        self._server_logger.info(f"RabbitMQ host:{host}, port:{rabbit_mq_port}")
        self._server_logger.info(f"Operandi MongoDB URL: {DB_URL}")

        self.app = self.__initiate_fast_api_app()

        # The following lines reuse the routers from the OCR-D WebAPI
        self.app.include_router(discovery.router)
        self.app.include_router(workflow.router)
        self.app.include_router(workspace.router)
        # Don't put this out of comments yet - missing config files/malfunctioning
        # self.app.include_router(processor.router)

        self.__publisher = self.__initiate_publisher(
            rabbit_mq_host,
            rabbit_mq_port,
            logger_name="operandi-server_publisher_server-queue"
        )
        self.__publisher.create_queue(
            queue_name=DEFAULT_QUEUE_SERVER_TO_BROKER,
            exchange_name=DEFAULT_EXCHANGER_NAME,
            exchange_type=DEFAULT_EXCHANGER_TYPE
        )

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

        @self.app.post("/workspace/import_external", tags=["Workspace"])
        async def operandi_import_from_mets_url(mets_url: str):
            bag_path = bagit_from_url(mets_url=mets_url, file_grp="DEFAULT")
            ws_url, ws_id = await self.workspace_manager.create_workspace_from_zip(bag_path, file_stream=False)

            # Note, this only posts the mets_url and do not
            # trigger a workflow execution, unlike the old api call

            return WorkspaceRsrc.create(workspace_url=ws_url, description="Workspace from Mets URL")

        @self.app.post("/workspace/import_local", tags=["Workspace"])
        async def operandi_import_from_mets_dir(mets_dir: str):
            ws_url, ws_id = await self.workspace_manager.create_workspace_from_mets_dir(mets_dir)
            return WorkspaceRsrc.create(workspace_url=ws_url, description="Workspace from Mets URL")

        """
        # Used to accept Mets URLs from the user
        @self.app.post("/mets_url")
        async def operandi_post_mets_url(mets_url: str, workspace_id: str):
            # Create a timestamp
            timestamp = datetime.datetime.now().strftime("_%Y%m%d_%H%M")
            # Append the timestamp at the end of the provided workspace_id
            workspace_id += timestamp
            publish_message = f"{mets_url},{workspace_id}".encode('utf8')

            self.__publisher.publish_to_queue(
                exchange_name=DEFAULT_EXCHANGER_NAME,
                queue_name=DEFAULT_QUEUE_SERVER_TO_BROKER,
                message=publish_message,
            )

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
        """

    def __initiate_fast_api_app(self):
        app = FastAPI(
            title="OPERANDI Server",
            description="REST API of the OPERANDI",
            license={
                "name": "Apache 2.0",
                "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
            },
            version="1.2.0",
            servers=[{
                "url": self.server_path,
                "description": "The URL of the OPERANDI server.",
            }],
        )

        return app

    @staticmethod
    def __initiate_publisher(rabbit_mq_host, rabbit_mq_port, logger_name):
        publisher = RMQPublisher(
            host=rabbit_mq_host,
            port=rabbit_mq_port,
            vhost="/",
            logger_name=logger_name
        )
        publisher.authenticate_and_connect(
            username="operandi-server",
            password="operandi-server"
        )
        publisher.enable_delivery_confirmations()
        return publisher
