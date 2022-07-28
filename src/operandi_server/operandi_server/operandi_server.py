import os
import datetime
from shutil import make_archive
from fastapi import FastAPI
from fastapi.responses import FileResponse
from typing import Optional
from priority_queue.producer import Producer
from priority_queue.constants import (
    RABBIT_MQ_HOST,
    RABBIT_MQ_PORT
)
from .constants import (
    SERVER_HOST as HOST,
    SERVER_PORT as PORT,
    SERVER_PATH,
    PRESERVE_REQUESTS,
)


class OperandiServer:
    def __init__(self,
                 host=HOST,
                 port=PORT,
                 rabbit_mq_host=RABBIT_MQ_HOST,
                 rabbit_mq_port=RABBIT_MQ_PORT):
        self.host = host
        self.port = port
        self.server_path = SERVER_PATH
        self.preserve_requests = PRESERVE_REQUESTS
        self._home_dir_path = os.path.expanduser("~")

        self.vd18_id_dict = {}
        self.producer = Producer(
            username="operandi-server",
            password="operandi-server",
            rabbit_mq_host=rabbit_mq_host,
            rabbit_mq_port=rabbit_mq_port
        )

        self.app = FastAPI(
            title="OPERANDI Server",
            description="REST API of the OPERANDI",
            license={
                "name": "Apache 2.0",
                "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
            },
            version="1.0.0",
            servers=[{
                "url": self.server_path,
                "description": "The URL of the OPERANDI server.",
            }],
        )

        # On startup reads the dictionary of IDs that were previously submitted
        # If PRESERVE_REQUESTS is True
        @self.app.on_event("startup")
        async def startup_event():
            if not self.preserve_requests:
                return
            if os.path.exists("vd18_ids.txt") and os.path.isfile("vd18_ids.txt"):
                with open("vd18_ids.txt", mode="r") as backup_doc:
                    for line in backup_doc:
                        line = line.strip('\n')
                        key, value = line.split(',')
                        self.vd18_id_dict[key] = value

            # Initialize the listener (listens for job_id replies)
            self.producer.define_consuming_listener(
                callback=self.job_id_callback
            )

        # On shutdown writes the dictionary of IDs to a text file
        # If PRESERVE_REQUESTS is True
        @self.app.on_event("shutdown")
        def shutdown_event():
            if not self.preserve_requests:
                return
            if len(self.vd18_id_dict):
                with open("vd18_ids.txt", mode="w") as backup_doc:
                    for k in self.vd18_id_dict:
                        backup_doc.write(f"{k}, {self.vd18_id_dict[k]}\n")

        @self.app.get("/")
        async def home():
            message = "The home page of OPERANDI server"
            time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            return {"message": message, "time": time}

        # Basic dummy requests support without appropriate response models
        @self.app.get("/vd18_ids/")
        async def get_vd18_ids(start: Optional[int] = None, end: Optional[int] = None):
            if start and end:
                message = f"Dict of vd18 ids in index range {start}-{end}: {self.vd18_id_dict[start:end]}"
                return {"message": message}
            else:
                message = f"Complete dict of vd18 ids: {self.vd18_id_dict}"
                return {"message": message}

        @self.app.get("/vd18_ids/{vd18_id}")
        async def get_vd18_id(vd18_id: str):
            message = f"{vd18_id} was not found!"
            if vd18_id in self.vd18_id_dict:
                message = f"ID:{vd18_id} found!"
            return {"message": message}

        # TODO: The two methods below could and should be combined
        # To keep it simple, currently, both ways are supported

        # Used to accept VD18 IDs from the Harvester
        @self.app.post("/vd18_ids/")
        async def post_vd18_id(vd18_url: str, vd18_id: str):
            message = f"{vd18_id} was already posted!"
            if vd18_id not in self.vd18_id_dict:
                self.vd18_id_dict[vd18_id] = vd18_url
                publish_message = f"{self.vd18_id_dict[vd18_id]},{vd18_id}"
                # Send the posted vd18_id to the priority queue
                self.producer.publish_mets_url(publish_message.encode('utf8'))
                message = f"{vd18_id} is posted!"

            return {"message": message}

        # Used to accept Mets URLs from the user
        @self.app.post("/mets_url/")
        async def post_mets_url(mets_url: str, workspace_id: str):
            # Create a timestamp
            timestamp = datetime.datetime.now().strftime("_%Y%m%d_%H%M")
            # Append the timestamp at the end of the provided workspace_id
            workspace_id += timestamp
            publish_message = f"{mets_url},{workspace_id}".encode('utf8')

            # Send the posted mets_url to the priority queue
            self.producer.publish_mets_url(body=publish_message)

            # TODO: Replace this properly so a thread handles that
            # TODO: Thread
            # Blocks here till the job id is received back
            job_id = self.producer.receive_job_id()
            # print(f"JobID:{job_id}")

            message = f"Mets URL posted successfully!"
            return {"message": message, "mets_url": mets_url, "workspace_id": workspace_id, "job_id": job_id}

        # List available workspaces
        @self.app.get("/workspaces/")
        async def get_workspaces():
            local_workspace_path = f"{self._home_dir_path}/OPERANDI_DATA/ws_local"
            # For the Alpha release only mockup is used, so no hpc workspace checked
            # hpc_workspace_path = f"{self._home_dir_path}/OPERANDI_DATA/ws_hpc"

            workspaces = []
            for filename in os.listdir(local_workspace_path):
                workspace = os.path.join(local_workspace_path, filename)
                if os.path.isdir(workspace):
                    workspaces.append(filename)

            return {"workspaces": workspaces}

        # Download workspace
        @self.app.get("/workspaces/workspace_id")
        async def get_workspaces(workspace_id: str):
            local_workspace_path = f"{self._home_dir_path}/OPERANDI_DATA/ws_local"
            workspace_path = f"{local_workspace_path}/{workspace_id}"
            # For the Alpha release only mockup is used, so no hpc workspace checked
            # hpc_workspace_path = f"{self._home_dir_path}/OPERANDI_DATA/ws_hpc"

            if os.path.exists(workspace_path) and \
                    os.path.isdir(workspace_path):
                make_archive(workspace_path, "zip", workspace_path)
                return FileResponse(path=f"{workspace_path}.zip",
                                    media_type='application/zip',
                                    filename=f"{workspace_id}.zip")
            else:
                message = f"workspace with id: {workspace_id} was not found!"
                return {"message": message}

        # --- Callback functions called based on Service broker responses --- #
        # Callback for jobID - currently not used, will be used by a thread
        # TODO: Handle with a thread
        # TODO: Use this callback function instead of "self.producer.receive_job_id()"
        def job_id_callback(self, ch, method, properties, body):
            # print(f"{self}")
            # print(f"INFO: ch: {ch}")
            # print(f"INFO: method: {method}")
            # print(f"INFO: properties: {properties}")

            if body:
                job_id = body.decode('utf8')
                # print(f"INFO: ch: {ch}")
                # print(f"INFO: method: {method}")
                # print(f"INFO: properties: {properties}")
                print(f"INFO: A JobID has been received: {job_id}")
                return job_id
