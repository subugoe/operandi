from datetime import datetime
from logging import getLogger
from os import environ
from uvicorn import run

from fastapi import FastAPI, status

from operandi_utils import get_log_file_path_prefix, reconfigure_all_loggers, verify_database_uri
from operandi_utils.constants import AccountType, LOG_LEVEL_SERVER, OPERANDI_VERSION
from operandi_utils.database import db_initiate_database
from operandi_utils import safe_init_logging

from operandi_server.constants import (
    SERVER_OTON_CONVERSIONS, SERVER_WORKFLOW_JOBS_ROUTER, SERVER_WORKFLOWS_ROUTER, SERVER_WORKSPACES_ROUTER)
from operandi_server.files_manager import create_resource_base_dir
from operandi_server.routers import RouterAdminPanel, RouterDiscovery, RouterUser, RouterWorkflow, RouterWorkspace
from operandi_server.routers.user_utils import create_user_if_not_available



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

        self.logger = getLogger("operandi_server.server")
        self.live_server_url = live_server_url
        self.local_server_url = local_server_url

        try:
            self.db_url = verify_database_uri(db_url)
            self.logger.debug(f'Verified MongoDB URL: {db_url}')
            self.rabbitmq_url = rabbitmq_url
        except ValueError as e:
            raise ValueError(e)

        self.rmq_publisher = None

        live_server_80 = {"url": self.live_server_url, "description": "The URL of the live OPERANDI server."}
        local_server = {"url": self.local_server_url, "description": "The URL of the local OPERANDI server."}
        server_license = {"name": "Apache 2.0", "url": "http://www.apache.org/licenses/LICENSE-2.0.html"}
        super().__init__(
            title="OPERANDI Server",
            description="REST API of the OPERANDI",
            version=OPERANDI_VERSION,
            license=server_license,
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
        self.logger.info(f"Operandi local server url: {self.local_server_url}")
        self.logger.info(f"Operandi live server url: {self.live_server_url}")

        # TODO: Recheck this again...
        safe_init_logging()
        log_file_path = f"{get_log_file_path_prefix(module_type='server')}.log"
        # Reconfigure all loggers to the same format
        reconfigure_all_loggers(log_level=LOG_LEVEL_SERVER, log_file_path=log_file_path)

        create_resource_base_dir(SERVER_OTON_CONVERSIONS)
        create_resource_base_dir(SERVER_WORKFLOW_JOBS_ROUTER)
        create_resource_base_dir(SERVER_WORKFLOWS_ROUTER)
        create_resource_base_dir(SERVER_WORKSPACES_ROUTER)

        # Initiate database client
        await db_initiate_database(self.db_url)

        # Insert the default server and harvester credentials to the DB
        await self.insert_default_accounts()

        # Include the endpoints of the OCR-D WebAPI
        await self.include_webapi_routers()

    async def shutdown_event(self):
        # TODO: Gracefully shutdown and clean things here if needed
        self.logger.info(f"The Operandi Server is shutting down.")

    async def home(self):
        message = f"The home page of the {self.title}"
        _time = datetime.now().strftime("%Y-%m-%d %H:%M")
        json_message = {
            "message": message,
            "time": _time
        }
        return json_message

    async def include_webapi_routers(self):
        self.include_router(RouterAdminPanel().router)
        self.include_router(RouterDiscovery().router)
        self.include_router(RouterUser().router)
        workflow_router = RouterWorkflow()
        await workflow_router.produce_production_workflows()
        await workflow_router.insert_production_workflows()
        self.include_router(workflow_router.router)
        self.include_router(RouterWorkspace().router)

    async def insert_default_accounts(self):
        default_admin_user = environ.get("OPERANDI_SERVER_DEFAULT_USERNAME", None)
        default_admin_pass = environ.get("OPERANDI_SERVER_DEFAULT_PASSWORD", None)
        default_harvester_user = environ.get("OPERANDI_HARVESTER_DEFAULT_USERNAME", None)
        default_harvester_pass = environ.get("OPERANDI_HARVESTER_DEFAULT_PASSWORD", None)

        self.logger.info(f"Configuring default server admin account")
        if default_admin_user and default_admin_pass:
            await create_user_if_not_available(
                self.logger,
                username=default_admin_user,
                password=default_admin_pass,
                account_type=AccountType.ADMIN,
                institution_id="GWDG Goettingen",
                approved_user=True,
                details="Default admin account"
            )
            self.logger.info(f"Inserted default server account credentials")

        self.logger.info(f"Configuring default harvester account")
        if default_harvester_user and default_harvester_pass:
            await create_user_if_not_available(
                self.logger,
                username=default_harvester_user,
                password=default_harvester_pass,
                account_type=AccountType.HARVESTER,
                institution_id="SUB Goettingen",
                approved_user=True,
                details="Default harvester account"
            )
            self.logger.info(f"Inserted default harvester account credentials")
