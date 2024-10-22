"""
module for implementing the discovery section of the api
"""
from logging import getLogger
from os import cpu_count
from psutil import virtual_memory
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils.constants import ServerApiTag
from operandi_server.models import PYDiscovery
from .user import RouterUser


class RouterDiscovery:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.discovery")
        self.user_authenticator = RouterUser()

        self.router = APIRouter(tags=[ServerApiTag.DISCOVERY])
        self.router.add_api_route(
            path="/discovery",
            endpoint=self.discovery, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="List Operandi Server properties",
            response_model=PYDiscovery, response_model_exclude_unset=True, response_model_exclude_none=True
        )

    async def discovery(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> PYDiscovery:
        await self.user_authenticator.user_login(auth)
        response = PYDiscovery(
            ram=virtual_memory().total / (1024.0 ** 3),
            cpu_cores=cpu_count(),
            has_cuda=False,
            cuda_version="Cuda not available",
            has_ocrd_all=False,
            ocrd_all_version="OCR-D all not available",
            has_docker=False
        )
        return response
