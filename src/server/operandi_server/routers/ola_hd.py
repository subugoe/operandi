from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils.constants import ServerApiTag
from operandi_server.models import OlahdUploadArguments
from .ola_hd_utils import send_bag_to_ola_hd
from .user_utils import user_auth_with_handling
from .workspace_utils import create_workspace_bag, get_db_workspace_with_handling, validate_bag_with_handling


class RouterOlahd:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.olahd")
        self.router = APIRouter(tags=[ServerApiTag.OLAHD])
        self.add_api_routes(self.router)

    def add_api_routes(self, router: APIRouter):
        router.add_api_route(
            path="/push_to_ola_hd",
            endpoint=self.push_to_ola_hd, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="Push a workspace to Ola-HD service"
        )

    async def push_to_ola_hd(
        self, workspace_id: str, olahd_args: OlahdUploadArguments, auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ):
        await user_auth_with_handling(self.logger, auth)
        db_workspace = await get_db_workspace_with_handling(self.logger, workspace_id=workspace_id)
        try:
            bag_dst = create_workspace_bag(db_workspace=db_workspace)
        except Exception as error:
            message = f"Failed to create workspace bag for: {workspace_id}"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
        validate_bag_with_handling(self.logger, bag_dst=bag_dst)

        try:
            pid = send_bag_to_ola_hd(
                path_to_bag=bag_dst,
                username=olahd_args.username,
                password=olahd_args.password,
                endpoint=olahd_args.endpoint
            )
        except Exception as error:
            message = "Failed to send bag to Ola-HD service"
            self.logger.error(f"{message}, error: {error}")
            try:
                response_status_code = error.response.status_code
            except AttributeError:
                response_status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            raise HTTPException(status_code=response_status_code, detail=message)

        response_message = {
            "message": f"Workspace bag of id: {workspace_id} was pushed to the Ola-HD service",
            "pid": pid
        }
        return response_message
