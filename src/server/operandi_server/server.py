from datetime import datetime
from logging import getLogger
from os import environ
from typing import List
from uvicorn import run
from fastapi import FastAPI, status

from operandi_utils import get_log_file_path_prefix, reconfigure_all_loggers, verify_database_uri
from operandi_utils.constants import LOG_LEVEL_SERVER, OPERANDI_VERSION
from operandi_utils.database import db_initiate_database
from operandi_utils import safe_init_logging

from operandi_server.files_manager import LFMInstance
from operandi_server.routers import (
    RouterAdminPanel, RouterDiscovery, RouterOlahd, RouterOton, RouterUser, RouterWorkflow, RouterWorkspace)
from operandi_server.server_utils import (
    insert_default_accounts, insert_production_workflows, produce_production_workflows)


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
        self.production_workflows: List[str] = []

        try:
            self.db_url = verify_database_uri(db_url)
            self.logger.debug(f'Verified MongoDB URL: {db_url}')
            self.rabbitmq_url = rabbitmq_url
        except ValueError as e:
            raise ValueError(e)

        self.rmq_publisher = None
        super().__init__(
            title="OPERANDI Server",
            description="REST API of the OPERANDI",
            version=OPERANDI_VERSION,
            license={"name": "Apache 2.0", "url": "http://www.apache.org/licenses/LICENSE-2.0.html"},
            servers=[
                {"url": self.live_server_url, "description": "The URL of the live OPERANDI server."},
                {"url": self.local_server_url, "description": "The URL of the local OPERANDI server."}
            ],
            on_startup=[self.startup_event],
            on_shutdown=[self.shutdown_event]
        )
        self.add_api_routes()

    def add_api_routes(self):
        self.router.add_api_route(
            path="/",
            endpoint=self.home, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get information about the server"
        )

    def run_server(self):
        host, port = self.local_server_url.split("//")[1].split(":")
        run(self, host=host, port=int(port))

    async def startup_event(self):
        self.logger.info(f"Operandi local server url: {self.local_server_url}")
        self.logger.info(f"Operandi live server url: {self.live_server_url}")

        safe_init_logging()
        log_file_path = f"{get_log_file_path_prefix(module_type='server')}.log"
        # Reconfigure all loggers to the same format
        reconfigure_all_loggers(log_level=LOG_LEVEL_SERVER, log_file_path=log_file_path)

        LFMInstance.make_dir_base_resources()

        # Initiate database client
        await db_initiate_database(self.db_url)
        await insert_default_accounts(self.logger)
        await produce_production_workflows(self.logger)
        self.production_workflows = await insert_production_workflows(self.logger)
        await self.include_webapi_routers()

    async def shutdown_event(self):
        self.logger.info(f"The Operandi Server is shutting down.")

    async def home(self):
        message = f"The home page of the {self.title}"
        _time = datetime.now().strftime("%Y-%m-%d %H:%M")
        json_message = {"message": message, "time": _time}
        return json_message

    async def include_webapi_routers(self):
        self.include_router(RouterAdminPanel().router)
        self.include_router(RouterDiscovery().router)
        self.include_router(RouterOlahd().router)
        self.include_router(RouterOton().router)
        self.include_router(RouterUser().router)
        self.include_router(RouterWorkflow(self.production_workflows).router)
        self.include_router(RouterWorkspace().router)
