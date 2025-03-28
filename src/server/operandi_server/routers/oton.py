from logging import getLogger
from os.path import join

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from operandi_utils.constants import ServerApiTag
from operandi_server.files_manager import LFMInstance, receive_resource
from .oton_utils import convert_oton_with_handling, validate_oton_with_handling
from .user_utils import user_auth_with_handling


class RouterOton:
    def __init__(self):
        self.logger = getLogger("operandi_server.routers.oton")
        self.router = APIRouter(tags=[ServerApiTag.OTON])
        self.add_api_routes(self.router)

    def add_api_routes(self, router: APIRouter):
        router.add_api_route(
            path="/convert_workflow",
            endpoint=self.convert_txt_to_nextflow, methods=["POST"], status_code=status.HTTP_201_CREATED,
            summary="""
            Upload a text file containing a workflow in ocrd process format and
            convert it to a Nextflow script in the desired format (local/docker/apptainer)
            """,
            response_model=None, response_model_exclude_unset=False, response_model_exclude_none=False
        )

    async def convert_txt_to_nextflow(
        self, txt_file: UploadFile, environment: str, with_mets_server: bool = True,
        auth: HTTPBasicCredentials = Depends(HTTPBasic())
    ):
        await user_auth_with_handling(self.logger, auth)
        oton_id, oton_dir = LFMInstance.make_dir_oton_conversions()
        ocrd_process_txt = join(oton_dir, f"ocrd_process_input.txt")
        nf_script_dest = join(oton_dir, f"nextflow_output.nf")

        try:
            await receive_resource(file=txt_file, resource_dst=ocrd_process_txt)
        except Exception as error:
            message = "Failed to receive the workflow resource"
            self.logger.error(f"{message}, error: {error}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

        await validate_oton_with_handling(self.logger, ocrd_process_txt)
        await convert_oton_with_handling(self.logger, ocrd_process_txt, nf_script_dest, environment, with_mets_server)
        return FileResponse(nf_script_dest, filename=f'{oton_id}.nf', media_type="application/txt-file")
