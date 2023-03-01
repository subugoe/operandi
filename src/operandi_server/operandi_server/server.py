import datetime
import logging
import json

from fastapi import FastAPI

import ocrd_webapi.database as db
from ocrd_webapi.exceptions import ResponseException
from ocrd_webapi.managers.workspace_manager import WorkspaceManager
from ocrd_webapi.managers.workflow_manager import WorkflowManager
from ocrd_webapi.models.workspace import WorkspaceRsrc
from ocrd_webapi.models.workflow import WorkflowJobRsrc
from ocrd_webapi.rabbitmq import RMQPublisher
from ocrd_webapi.routers import discovery, workflow, workspace
from ocrd_webapi.utils import bagit_from_url

from .constants import (
    # Requests coming from the Harvester are sent to this queue
    DEFAULT_QUEUE_FOR_HARVESTER,
    # Requests coming from other users are sent to this queue
    DEFAULT_QUEUE_FOR_USERS,
    LIVE_SERVER_URL
)
from .models import WorkflowArguments


class OperandiServer:
    def __init__(self, host, port, server_url, db_url, rmq_host, rmq_port, rmq_vhost):
        self.log = logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.server_url = server_url
        self.db_url = db_url

        self.rmq_host = rmq_host
        self.rmq_port = rmq_port
        self.rmq_vhost = rmq_vhost

        # These are initialized on startup_event of the server
        self.rmq_publisher = None
        self.workflow_manager = None
        self.workspace_manager = None

        self.app = self.initiate_fast_api_app()

        @self.app.on_event("startup")
        async def startup_event():
            self.log.info(f"Operandi server url: {self.server_url}")

            # Initiate database client
            await db.initiate_database(self.db_url)

            # Connect the publisher to the RabbitMQ Server
            self.connect_publisher(
                username="default-publisher",
                password="default-publisher",
                enable_acks=True
            )

            # Create the message queues (nothing happens if they already exist)
            self.rmq_publisher.create_queue(queue_name=DEFAULT_QUEUE_FOR_HARVESTER)
            self.rmq_publisher.create_queue(queue_name=DEFAULT_QUEUE_FOR_USERS)

            # Include the endpoints of the OCR-D WebAPI
            self.include_webapi_routers()

            # Used to extend/overwrite the Workflow routing endpoint of the OCR-D WebAPI
            self.workflow_manager = WorkflowManager()
            # Used to extend/overwrite the Workspace routing endpoint of the OCR-D WebAPI
            self.workspace_manager = WorkspaceManager()

        @self.app.on_event("shutdown")
        def shutdown_event():
            # TODO: Gracefully shutdown and clean things here if needed
            self.log.info(f"The Operandi Server is shutting down.")

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
            return WorkspaceRsrc.create(
                workspace_id=ws_id,
                workspace_url=ws_url,
                description="Workspace from Mets URL"
            )

        # Submits a workflow execution request to the RabbitMQ
        @self.app.post("/workflow/run_workflow/{user_id}", tags=["Workflow"])
        async def operandi_run_workflow(user_id: str, workflow_args: WorkflowArguments):
            try:
                # Extract workflow arguments
                workspace_id = workflow_args.workspace_id
                workflow_id = workflow_args.workflow_id

                # Create job request parameters
                job_id, job_dir_path = self.workflow_manager.create_workflow_execution_space(workflow_id)
                job_state = "QUEUED"

                # Build urls to be sent as a response
                workspace_url = self.workspace_manager.get_resource(workspace_id, local=False)
                workflow_url = self.workflow_manager.get_resource(workflow_id, local=False)
                job_url = self.workflow_manager.get_resource_job(workflow_id, job_id, local=False)

                # Save to the workflow job to the database
                await db.save_workflow_job(
                    workspace_id=workspace_id,
                    workflow_id=workflow_id,
                    job_id=job_id,
                    job_path=job_dir_path,
                    job_state=job_state
                )

                # Create the message to be sent to the RabbitMQ queue
                workflow_processing_message = {
                    "workflow_id": f"{workflow_id}",
                    "workspace_id": f"{workspace_id}",
                    "job_id": f"{job_id}"
                }
                encoded_workflow_message = json.dumps(workflow_processing_message)

                # Send the message to a queue based on the user_id
                if user_id == "harvester":
                    self.rmq_publisher.publish_to_queue(
                        queue_name=DEFAULT_QUEUE_FOR_HARVESTER,
                        message=encoded_workflow_message
                    )
                else:
                    self.rmq_publisher.publish_to_queue(
                        queue_name=DEFAULT_QUEUE_FOR_USERS,
                        message=encoded_workflow_message
                    )
            except Exception as error:
                self.log.error(f"SERVER ERROR: {error}")
                raise ResponseException(500, {"error": f"internal server error: {error}"})

            return WorkflowJobRsrc.create(
                job_id=job_id,
                job_url=job_url,
                workflow_id=workflow_id,
                workflow_url=workflow_url,
                workspace_id=workspace_id,
                workspace_url=workspace_url,
                job_state=job_state
            )

        """
        This causes problems in the WebAPI part. Disabled for now.
        
        @self.app.post("/workspace/import_local", tags=["Workspace"])
        async def operandi_import_from_mets_dir(mets_dir: str):
            ws_url, ws_id = await self.workspace_manager.create_workspace_from_mets_dir(mets_dir)
            return WorkspaceRsrc.create(workspace_url=ws_url, description="Workspace from Mets URL")
        """

    def initiate_fast_api_app(self):
        live_server_80 = {"url": LIVE_SERVER_URL, "description": "The URL of the live OPERANDI server."}
        local_server = {"url": self.server_url, "description": "The URL of the local OPERANDI server."}
        app = FastAPI(
            title="OPERANDI Server",
            description="REST API of the OPERANDI",
            license={
                "name": "Apache 2.0",
                "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
            },
            version="1.4.3",
            servers=[live_server_80, local_server]
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
