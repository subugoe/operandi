"""
module for implementing the discovery section of the api
"""
from json import JSONDecodeError
from logging import getLogger
from os import cpu_count
from psutil import virtual_memory
from typing import List, Dict
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils.constants import ServerApiTag
from operandi_utils.oton.constants import OCRD_ALL_JSON
from operandi_server.models import PYDiscovery
from .user_utils import user_auth_with_handling


class RouterDiscovery:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.discovery")

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
        self.router.add_api_route(
            path="/discovery/processor/{processor_name}",
            endpoint=self.get_processor_info, methods=["GET"], status_code=status.HTTP_200_OK,
            summary="Get information about a specific OCR-D processor"
        )

    async def discovery(self, auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> PYDiscovery:
        await user_auth_with_handling(self.logger, auth)
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
        await user_auth_with_handling(self.logger, auth)
        try:
            processor_names = list(OCRD_ALL_JSON.keys())
            return processor_names
        except JSONDecodeError as e:
            message = f"Error decoding processor data file: {str(e)}"
            self.logger.error(message)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
        except Exception as e:
            self.logger.error(f"Unexpected error while loading processors: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while loading processor names.")

    async def get_processor_info(self, processor_name: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())) -> Dict:
        await user_auth_with_handling(self.logger, auth)
        try:
            if processor_name not in OCRD_ALL_JSON:
                raise HTTPException(status_code=404, detail=f"Processor '{processor_name}' not found.")
            processor_info = OCRD_ALL_JSON[processor_name]
            return processor_info
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Error decoding processor data file.")
        except Exception as e:
            self.logger.error(f"Error retrieving processor info for {processor_name}: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred.")
