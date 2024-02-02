from datetime import datetime
from logging import getLogger
from os import environ
from uvicorn import run

from fastapi import FastAPI, status

from operandi_utils import get_log_file_path_prefix, reconfigure_all_loggers, verify_database_uri
from operandi_utils.constants import LOG_LEVEL_SERVER, OPERANDI_VERSION
from operandi_utils.database import db_initiate_database
from operandi_server.authentication import create_user_if_not_available
from operandi_server.constants import SERVER_WORKFLOW_JOBS_ROUTER, SERVER_WORKFLOWS_ROUTER, SERVER_WORKSPACES_ROUTER
from operandi_server.files_manager import create_resource_base_dir
from operandi_server.routers import RouterDiscovery, user, workflow, workspace
from operandi_server.utils import safe_init_logging


class OperandiServer(FastAPI):
    def __init__(
        self,
        db_url: str = environ.get("OPERANDI_DB_URL"),
        rabbitmq_url: str = environ.get("OPERANDI_RABBITMQ_URL"),
        live_server_url: str = environ.get("OPERANDI_SERVER_URL_LIVE"),
        local_server_url: str = environ.get("OPERANDI_SERVER_URL_LOCAL")
    ):
        if not db_url:
            raise ValueError("Environment variable not set: OPERANDI_DB_URL")
        if not rabbitmq_url:
            raise ValueError("Environment variable not set: OPERANDI_RABBITMQ_URL")
        if not live_server_url:
            raise ValueError("Environment variable not set: OPERANDI_SERVER_URL_LIVE")
        if not local_server_url:
            raise ValueError("Environment variable not set: OPERANDI_SERVER_URL_LOCAL")

        self.log = getLogger("operandi_server.server")
        self.live_server_url = live_server_url
        self.local_server_url = local_server_url

        try:
            self.db_url = verify_database_uri(db_url)
            self.log.debug(f'Verified MongoDB URL: {db_url}')
            self.rabbitmq_url = rabbitmq_url
        except ValueError as e:
            raise ValueError(e)

        self.rmq_publisher = None

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

    def run_server(self):
        host, port = self.local_server_url.split("//")[1].split(":")
        run(self, host=host, port=int(port))

    async def startup_event(self):
        self.log.info(f"Operandi local server url: {self.local_server_url}")
        self.log.info(f"Operandi live server url: {self.live_server_url}")

        # TODO: Recheck this again...
        safe_init_logging()
        log_file_path = f"{get_log_file_path_prefix(module_type='server')}.log"
        # Reconfigure all loggers to the same format
        reconfigure_all_loggers(log_level=LOG_LEVEL_SERVER, log_file_path=log_file_path)

        create_resource_base_dir(SERVER_WORKFLOW_JOBS_ROUTER)
        create_resource_base_dir(SERVER_WORKFLOWS_ROUTER)
        create_resource_base_dir(SERVER_WORKSPACES_ROUTER)

        # Initiate database client
        await db_initiate_database(self.db_url)

        # Insert the default server and harvester credentials to the DB
        await self.insert_default_credentials()

        # Include the endpoints of the OCR-D WebAPI
        self.include_webapi_routers()

    async def shutdown_event(self):
        # TODO: Gracefully shutdown and clean things here if needed
        self.log.info(f"The Operandi Server is shutting down.")

    async def home(self):
        message = f"The home page of the {self.title}"
        _time = datetime.now().strftime("%Y-%m-%d %H:%M")
        json_message = {
            "message": message,
            "time": _time
        }
        return json_message

    def include_webapi_routers(self):
        self.include_router(RouterDiscovery().router)
        self.include_router(user.router)
        self.include_router(workflow.router)
        self.include_router(workspace.router)

    async def insert_default_credentials(self):
        default_admin_user = environ.get("OPERANDI_SERVER_DEFAULT_USERNAME", None)
        default_admin_pass = environ.get("OPERANDI_SERVER_DEFAULT_PASSWORD", None)
        default_harvester_user = environ.get("OPERANDI_HARVESTER_DEFAULT_USERNAME", None)
        default_harvester_pass = environ.get("OPERANDI_HARVESTER_DEFAULT_PASSWORD", None)

        self.log.info(f"Configuring default server auth")
        if default_admin_user and default_admin_pass:
            await create_user_if_not_available(
                username=default_admin_user,
                password=default_admin_pass,
                account_type="administrator",
                approved_user=True
            )
            self.log.info(f"Configured default server auth")

        self.log.info(f"Configuring default harvester auth")
        if default_harvester_user and default_harvester_pass:
            await create_user_if_not_available(
                username=default_harvester_user,
                password=default_harvester_pass,
                account_type="harvester",
                approved_user=True
            )
            self.log.info(f"Configured default harvester auth")
