import datetime
import logging

from fastapi import FastAPI

from ocrd_webapi.database import initiate_database
from ocrd_webapi.managers.workspace_manager import WorkspaceManager
from ocrd_webapi.models.workspace import WorkspaceRsrc
from ocrd_webapi.rabbitmq import RMQPublisher
from ocrd_webapi.routers import discovery, workflow, workspace
from ocrd_webapi.utils import bagit_from_url

from .constants import LOG_FORMAT, LOG_LEVEL


class OperandiServer:
    def __init__(self, host, port, server_url, db_url, rmq_host, rmq_port, rmq_vhost):
        self.log = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
        logging.getLogger(__name__).setLevel(LOG_LEVEL)

        self.host = host
        self.port = port
        self.server_url = server_url
        self.db_url = db_url

        self.rmq_host = rmq_host
        self.rmq_port = rmq_port
        self.rmq_vhost = rmq_vhost
        self.rmq_publisher = None

        # Used to extend the Workspace endpoint of the OCR-D WebAPI
        self.workspace_manager = WorkspaceManager()

        self.app = self.initiate_fast_api_app()
        self.include_webapi_routers()

        @self.app.on_event("startup")
        async def startup_event():
            self.log.info(f"Operandi server url: {self.server_url}")
            self.log.info(f"Connecting to the MongoDB URL: {self.db_url}")
            await initiate_database(self.db_url)

        @self.app.on_event("shutdown")
        def shutdown_event():
            self.log.info(f"The Operandi Server is shutting down.")
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

        """
        This causes problems in the WebAPI part. Disabled for now.
        
        @self.app.post("/workspace/import_local", tags=["Workspace"])
        async def operandi_import_from_mets_dir(mets_dir: str):
            ws_url, ws_id = await self.workspace_manager.create_workspace_from_mets_dir(mets_dir)
            return WorkspaceRsrc.create(workspace_url=ws_url, description="Workspace from Mets URL")
        """

    def initiate_fast_api_app(self):
        app = FastAPI(
            title="OPERANDI Server",
            description="REST API of the OPERANDI",
            license={
                "name": "Apache 2.0",
                "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
            },
            version="1.2.0",
            servers=[{
                "url": self.server_url,
                "description": "The URL of the OPERANDI server.",
            }],
        )
        return app

    def connect_publisher(
            self,
            username: str,
            password: str,
            enable_acks: bool = True
    ) -> None:
        self.log.info(f"Connecting RMQPublisher to RabbitMQ server: "
                      f"{self.rmq_host}:{self.rmq_port}{self.rmq_vhost}")
        self.rmq_publisher = RMQPublisher(
            host=self.rmq_host,
            port=self.rmq_port,
            vhost=self.rmq_vhost,
        )
        # TODO: Remove this information before the release
        self.log.debug(f"RMQPublisher authenticates with username: "
                       f"{username}, password: {password}")
        self.rmq_publisher.authenticate_and_connect(username=username, password=password)
        if enable_acks:
            self.rmq_publisher.enable_delivery_confirmations()
            self.log.debug(f"Delivery confirmations are enabled")
        else:
            self.log.debug(f"Delivery confirmations are disabled")
        self.log.debug(f"Successfully connected RMQPublisher.")

    def include_webapi_routers(self):
        self.app.include_router(discovery.router)
        # Don't put this out of comments yet - still missing
        # self.app.include_router(processor.router)
        self.app.include_router(workflow.router)
        self.app.include_router(workspace.router)
