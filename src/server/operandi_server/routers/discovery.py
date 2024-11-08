"""
module for implementing the discovery section of the api
"""
import json
from logging import getLogger
from os import cpu_count
from psutil import virtual_memory
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils.constants import ServerApiTag, OCRD_ALL_JSON
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
        self.router.add_api_route(
            path="/discovery/processors",
            endpoint=self.get_processor_names, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="List OCR-D processor names"
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

    async def get_processor_names(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> List[str]:
        # Authenticate the user
        await self.user_authenticator.user_login(auth)

        try:
            # Load JSON and extract processor names
            processor_names = list(OCRD_ALL_JSON.keys())
            return processor_names

        except FileNotFoundError:
            # Raise a 404 error if the JSON file is not found
            raise HTTPException(
                status_code=404,
                detail="Processor data file not found."
            )

        except json.JSONDecodeError:
            # Raise a 500 error if the JSON is invalid or cannot be parsed
            raise HTTPException(
                status_code=500,
                detail="Error decoding processor data file."
            )

        except Exception as e:
            # Raise a generic 500 error for any other exceptions
            self.logger.error(f"Unexpected error while loading processors: {e}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while loading processor names."
            )
