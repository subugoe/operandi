import os
import datetime
from pkg_resources import resource_filename

import uvicorn
from fastapi import FastAPI
from typing import Optional

from priority_queue.producer import Producer

from .constants import (
    SERVER_HOST as HOST,
    SERVER_PORT as PORT,
    SERVER_PATH,
    PRESERVE_REQUESTS,
)


class OperandiServer:
    def __init__(self, host=HOST, port=PORT):
        self.host = HOST
        self.port = PORT
        self.server_path = SERVER_PATH
        self.preserve_requests = PRESERVE_REQUESTS

        self.vd18_id_dict = {}
        self.producer = Producer()

        self.app = FastAPI(
            title="OPERANDI Server",
            description="REST API of the OPERANDI",
            license={
                "name": "Apache 2.0",
                "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
            },
            version="0.0.1",
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

        @self.app.post("/vd18_ids/")
        async def post_vd18_id(vd18_id: str, vd18_url: str):
            message = f"{vd18_id} was already posted!"
            if vd18_id not in self.vd18_id_dict:
                self.vd18_id_dict[vd18_id] = vd18_url
                publish_message = f"{vd18_id}, {self.vd18_id_dict[vd18_id]}"
                # Send the posted vd18_id to the priority queue
                self.producer.basic_publish(publish_message.encode('utf8'))
                message = f"{vd18_id} is posted!"

            return {"message": message}
