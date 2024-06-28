from logging import getLogger
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils.utils import send_bag_to_ola_hd
from operandi_server.models import PYUserAction
from .constants import ServerApiTags
from .user import RouterUser
from .workspace_utils import create_workspace_bag, get_db_workspace_with_handling, validate_bag_with_handling


class RouterAdminPanel:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.user")
        self.user_authenticator = RouterUser()
        self.router = APIRouter(tags=[ServerApiTags.ADMIN])
        self.router.add_api_route(
            path="/admin/push_to_ola_hd",
            endpoint=self.push_to_ola_hd, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="Push a workspace to Ola-HD service"
        )

    async def push_to_ola_hd(self, workspace_id: str, auth: HTTPBasicCredentials = Depends(HTTPBasic())):
        user_action = await self.user_authenticator.user_login(auth)
        if user_action.account_type != "ADMIN":
            message = f"Admin privileges required for the endpoint"
            self.logger.error(f"{message}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)
        db_workspace = await get_db_workspace_with_handling(self.logger, workspace_id=workspace_id)
        try:
            bag_dst = create_workspace_bag(db_workspace=db_workspace)
        except Exception as error:
            message = f"Failed to create workspace bag for: {workspace_id}"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)
        validate_bag_with_handling(self.logger, bag_dst=bag_dst)

        try:
            pid = send_bag_to_ola_hd(path_to_bag=bag_dst)
        except Exception as error:
            message = "Failed to send bag to Ola-HD service"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)

        response_message = {
            "message": f"Workspace bag of id: {workspace_id} was pushed to the Ola-HD service",
            "pid": pid
        }
        return response_message
