"""
module for implementing the discovery section of the api
"""
from os import cpu_count
from psutil import virtual_memory
from fastapi import APIRouter, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_server.models import DiscoveryResponse
from .user import user_login

router = APIRouter(tags=["Discovery"])

security = HTTPBasic()


class Discovery:
    @staticmethod
    def discovery() -> DiscoveryResponse:
        res = DiscoveryResponse()
        res.ram = virtual_memory().total / (1024.0 ** 3)
        res.cpu_cores = cpu_count()
        # TODO: Whether cuda is available or not
        res.has_cuda = False
        res.cuda_version = "Default: Cuda not available"
        # TODO: Whether ocrd-all (maximum) image is available or not
        res.has_ocrd_all = False
        res.ocrd_all_version = "Default: OCR-D not available"
        # TODO: Whether docker is installed or not
        res.has_docker = False
        return res


@router.get("/discovery", responses={"200": {"model": DiscoveryResponse}})
async def discovery(auth: HTTPBasicCredentials = Depends(security)) -> DiscoveryResponse:
    """
    Lists information about the Operandi Server.
    This is still not complete.

    Curl equivalent:
    `curl -X GET SERVER_ADDR/discovery`
    """
    await user_login(auth)
    return Discovery.discovery()
