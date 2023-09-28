"""
module for implementing the discovery section of the api
"""
from os import cpu_count
from psutil import virtual_memory
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_server.models import PYDiscovery
from .user import user_login


class RouterDiscovery:
    def __init__(self):
        self.router = APIRouter(tags=["Discovery"])
        self.router.add_api_route(
            path="/discovery",
            endpoint=self.discovery,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            summary="List Operandi Server properties",
            response_model=PYDiscovery,
            response_model_exclude_unset=True,
            response_model_exclude_none=True
        )

    @staticmethod
    async def discovery(
            auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ) -> PYDiscovery:
        await user_login(auth)
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
