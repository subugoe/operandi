import datetime
import logging
import json
from os import environ
from shutil import make_archive
import tempfile

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils import (
    OPERANDI_VERSION,
    reconfigure_all_loggers,
    verify_database_uri,
    verify_and_parse_mq_uri
)
import operandi_utils.database.database as db
from operandi_utils.rabbitmq import (
    # Requests coming from the
    # Harvester are sent to this queue
    DEFAULT_QUEUE_FOR_HARVESTER,
    # Requests coming from
    # other users are sent to this queue
    DEFAULT_QUEUE_FOR_USERS,
    # Requests for job status polling
    # are sent to this queue
    DEFAULT_QUEUE_FOR_JOB_STATUSES,
    RMQPublisher
)

from operandi_server.authentication import (
    AuthenticationError,
    authenticate_user,
    register_user
)
from operandi_server.constants import LOG_FILE_PATH, LOG_LEVEL
from operandi_server.exceptions import ResponseException
from operandi_server.models import (
    WorkflowArguments,
    WorkflowJobRsrc
)
from operandi_server.routers import discovery, user, workflow, workspace
from operandi_server.utils import safe_init_logging

security = HTTPBasic()


class OperandiServer(FastAPI):
    def __init__(self, live_server_url: str, local_server_url: str, db_url: str, rabbitmq_url: str):
        self.log = logging.getLogger(__name__)
        self.live_server_url = live_server_url
        self.local_server_url = local_server_url

        try:
            self.db_url = verify_database_uri(db_url)
            self.log.debug(f'Verified MongoDB URL: {db_url}')
            rmq_data = verify_and_parse_mq_uri(rabbitmq_url)
            self.log.debug(f'Verified RabbitMQ URL: {rabbitmq_url}')
            self.rmq_username = rmq_data['username']
            self.rmq_password = rmq_data['password']
            self.rmq_host = rmq_data['host']
            self.rmq_port = rmq_data['port']
            self.rmq_vhost = rmq_data['vhost']
            self.log.debug(f'Verified RabbitMQ Credentials: {self.rmq_username}:{self.rmq_password}')
            self.log.debug(f'Verified RabbitMQ Server URL: {self.rmq_host}:{self.rmq_port}{self.rmq_vhost}')
        except ValueError as e:
            raise ValueError(e)

        # These are initialized on startup_event of the server
        self.rmq_publisher = None
        self.workflow_manager = None
        self.workspace_manager = None

        live_server_80 = {"url": self.live_server_url, "description": "The URL of the live OPERANDI server."}
        local_server = {"url": self.local_server_url, "description": "The URL of the local OPERANDI server."}
        super().__init__(
            title="OPERANDI Server",
            description="REST API of the OPERANDI",
            version=OPERANDI_VERSION,
            license={
                "name": "Apache 2.0",
                "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
            },
            servers=[live_server_80, local_server],
            on_startup=[self.startup_event],
            on_shutdown=[self.shutdown_event]
        )

        self.router.add_api_route(
            path="/",
            endpoint=self.home,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            summary="Get information about the server"
        )

        self.router.add_api_route(
            path="/workflow/{workflow_id}",
            endpoint=self.submit_to_rabbitmq_queue,
            methods=["POST"],
            tags=["Workflow"],
            status_code=status.HTTP_201_CREATED,
            summary="Submit workflow job",
            response_model=WorkflowJobRsrc,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )

        self.router.add_api_route(
            path="/workflow/{workflow_id}/{job_id}",
            endpoint=self.get_workflow_job_status,
            methods=["GET"],
            tags=["Workflow"],
            status_code=status.HTTP_200_OK,
            summary="Check workflow job status",
            response_model=WorkflowJobRsrc,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )

    async def startup_event(self):
        self.log.info(f"Operandi local server url: {self.local_server_url}")
        self.log.info(f"Operandi live server url: {self.live_server_url}")

        # TODO: Recheck this again...
        safe_init_logging()

        # Reconfigure all loggers to the same format
        reconfigure_all_loggers(
            log_level=LOG_LEVEL,
            log_file_path=LOG_FILE_PATH
        )

        # Initiate database client
        await db.initiate_database(self.db_url)

        default_admin_user = environ.get("OPERANDI_SERVER_DEFAULT_USERNAME", None)
        default_admin_pass = environ.get("OPERANDI_SERVER_DEFAULT_PASSWORD", None)
        default_harvester_user = environ.get("OPERANDI_HARVESTER_DEFAULT_USERNAME", None)
        default_harvester_pass = environ.get("OPERANDI_HARVESTER_DEFAULT_PASSWORD", None)

        if default_admin_user and default_admin_pass:
            await self.create_user_if_not_available(
                username=default_admin_user,
                password=default_admin_pass,
                account_type="administrator",
                approved_user=True
            )

        if default_harvester_user and default_harvester_pass:
            await self.create_user_if_not_available(
                username=default_harvester_user,
                password=default_harvester_pass,
                account_type="harvester",
                approved_user=True
            )

        # Connect the publisher to the RabbitMQ Server
        self.connect_publisher(
            username=self.rmq_username,
            password=self.rmq_password,
            enable_acks=True
        )

        # Create the message queues (nothing happens if they already exist)
        self.rmq_publisher.create_queue(queue_name=DEFAULT_QUEUE_FOR_HARVESTER)
        self.rmq_publisher.create_queue(queue_name=DEFAULT_QUEUE_FOR_USERS)
        self.rmq_publisher.create_queue(queue_name=DEFAULT_QUEUE_FOR_JOB_STATUSES)

        # Include the endpoints of the OCR-D WebAPI
        self.include_webapi_routers()

        # Used to extend/overwrite the Workflow routing endpoint of the OCR-D WebAPI
        self.workflow_manager = workflow.workflow_manager
        # Used to extend/overwrite the Workspace routing endpoint of the OCR-D WebAPI
        self.workspace_manager = workspace.workspace_manager

    async def shutdown_event(self):
        # TODO: Gracefully shutdown and clean things here if needed
        self.log.info(f"The Operandi Server is shutting down.")

    @staticmethod
    async def create_user_if_not_available(username: str, password: str, account_type: str, approved_user: bool):
        # If the account is not available in the DB, create it
        try:
            await authenticate_user(username, password)
        except AuthenticationError:
            # TODO: Note that this account is never removed from
            #  the DB automatically in the current implementation
            await register_user(
                email=username,
                password=password,
                account_type=account_type,
                approved_user=approved_user
            )

    async def home(self):
        message = f"The home page of the {self.title}"
        _time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        json_message = {
            "message": message,
            "time": _time
        }
        return json_message

    async def get_workflow_job_status(
            self,
            workflow_id: str,
            job_id: str,
            accept: str = Header(default="application/json"),
            auth: HTTPBasicCredentials = Depends(security)
    ):
        """
        Get the status of a workflow job specified with `workflow_id` and `job_id`.
        Returns the `workflow_id`, `workspace_id`, `job_id`, and
        one of the following job statuses:
        1) QUEUED - The workflow job is queued for execution.
        2) RUNNING - The workflow job is currently running.
        3) STOPPED - The workflow job has failed.
        4) SUCCESS - The workflow job has finished successfully.

        Curl equivalent:
        `curl -X GET SERVER_ADDR/workflow/{workflow_id}/{job_id}`
        """
        await user.user_login(auth)
        # Create the job status message to be sent to the RabbitMQ queue
        job_status_message = {
            "job_id": f"{job_id}",
        }
        encoded_workflow_message = json.dumps(job_status_message)
        self.rmq_publisher.publish_to_queue(
            queue_name=DEFAULT_QUEUE_FOR_JOB_STATUSES,
            message=encoded_workflow_message
        )
        wf_job_db = await self.workflow_manager.get_workflow_job(job_id=job_id)
        if not wf_job_db:
            raise ResponseException(404, {"error": f"workflow job not found: {job_id}"})
        try:
            wf_job_url = self.workflow_manager.get_workflow_job_url(
                job_id=wf_job_db.job_id,
                workflow_id=wf_job_db.workflow_id
            )
            wf_job_local = self.workflow_manager.get_workflow_job_path(
                job_id=wf_job_db.job_id,
                workflow_id=wf_job_db.workflow_id
            )
            workflow_url = self.workflow_manager.get_workflow_url(wf_job_db.workflow_id)
            workspace_url = self.workspace_manager.get_workspace_url(wf_job_db.workspace_id)
            job_state = wf_job_db.job_state
        except Exception as e:
            self.log.exception(f"Unexpected error in get_workflow_job: {e}")
            # TODO: Don't provide the exception message to the outside world
            raise ResponseException(500, {"error": f"internal server error: {e}"})

        if accept == "application/vnd.zip":
            tempdir = tempfile.mkdtemp(prefix="ocrd-wf-job-zip-")
            job_archive_path = make_archive(
                base_name=f'{tempdir}/{job_id}',
                format='zip',
                root_dir=wf_job_local,
            )
            return FileResponse(job_archive_path)

        return WorkflowJobRsrc.create(
            job_id=job_id,
            job_url=wf_job_url,
            workflow_id=workflow_id,
            workflow_url=workflow_url,
            workspace_id=wf_job_db.workspace_id,
            workspace_url=workspace_url,
            job_state=job_state
        )

    # TODO: Move this method inside routers/workflow
    # Submits a workflow execution request to the RabbitMQ
    async def submit_to_rabbitmq_queue(
            self,
            workflow_id: str,
            workflow_args: WorkflowArguments,
            auth: HTTPBasicCredentials = Depends(security)
    ):
        try:
            user_action = await user.user_login(auth)
            user_account_type = user_action.account_type
        except Exception as error:
            self.log.error(f"Authentication error: {error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"WWW-Authenticate": "Basic"},
                detail=f"Invalid login credentials or unapproved account."
            )

        try:
            # Extract workflow arguments
            workspace_id = workflow_args.workspace_id
            input_file_grp = workflow_args.input_file_grp

            # Create job request parameters
            job_id, job_dir = self.workflow_manager.create_workflow_job_space()
            job_state = "QUEUED"

            # Build urls to be sent as a response
            workspace_url = self.workspace_manager.get_workspace_url(workspace_id=workspace_id)
            workflow_url = self.workflow_manager.get_workflow_url(workflow_id=workflow_id)
            job_url = self.workflow_manager.get_workflow_job_url(job_id=job_id, workflow_id=workflow_id)

            # Save to the workflow job to the database
            await db.save_workflow_job(
                job_id=job_id,
                job_dir=job_dir,
                job_state=job_state,
                workspace_id=workspace_id,
                workflow_id=workflow_id
            )

            # Create the message to be sent to the RabbitMQ queue
            workflow_processing_message = {
                "workflow_id": f"{workflow_id}",
                "workspace_id": f"{workspace_id}",
                "job_id": f"{job_id}",
                "input_file_grp": f"{input_file_grp}"
            }
            encoded_workflow_message = json.dumps(workflow_processing_message)

            # Send the message to a queue based on the user_id
            if user_account_type == "harvester":
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
        self.rmq_publisher.authenticate_and_connect(username=username, password=password)
        if enable_acks:
            self.rmq_publisher.enable_delivery_confirmations()
            self.log.debug(f"Delivery confirmations are enabled")
        else:
            self.log.debug(f"Delivery confirmations are disabled")
        self.log.debug(f"Successfully connected RMQPublisher.")

    def include_webapi_routers(self):
        self.include_router(discovery.router)
        # Don't put this out of comments yet - still missing
        # self.app.include_router(processor.router)
        self.include_router(user.router)
        self.include_router(workflow.router)
        self.include_router(workspace.router)
