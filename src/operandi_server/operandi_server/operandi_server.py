import datetime
import os
from typing import Optional

import uvicorn
from fastapi import FastAPI

from src.priority_queue.priority_queue.producer import Producer

from .constants import (
    SERVER_IP,
    SERVER_PORT,
    SERVER_PATH,
    PRESERVE_REQUESTS,
)

app = FastAPI(
    title="OPERANDI Server",
    description="REST API of the OPERANDI",
    license={
        "name": "Apache 2.0",
        "url": "http://www.apache.org/licenses/LICENSE-2.0.html",
    },
    version="0.0.1",
    servers=[
        {
            "url": SERVER_PATH,
            "description": "The URL of the OPERANDI server.",
        }
    ],
)

producer = Producer()
vd18_id_dict = {}


# On startup reads the dictionary of IDs that were previously submitted
# If PRESERVE_REQUESTS is True
@app.on_event("startup")
async def startup_event():
    if not PRESERVE_REQUESTS:
        return
    if os.path.exists("vd18_ids.txt") and os.path.isfile("vd18_ids.txt"):
        with open("vd18_ids.txt", mode="r") as backup_doc:
            for line in backup_doc:
                line = line.strip('\n')
                key, value = line.split(',')
                # print(f"Read: key={key}, value={value}")
                vd18_id_dict[key] = value


# On shutdown writes the dictionary of IDs to a text file
# If PRESERVE_REQUESTS is True
@app.on_event("shutdown")
def shutdown_event():
    if not PRESERVE_REQUESTS:
        return
    if len(vd18_id_dict):
        with open("vd18_ids.txt", mode="w") as backup_doc:
            for k in vd18_id_dict:
                backup_doc.write(f"{k}, {vd18_id_dict[k]}\n")
                # print(f"Write: key{k}, value={vd18_id_dict[k]}")


@app.get("/")
async def home():
    return {"message": "The home page of OPERANDI server",
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }


# Basic dummy requests support without appropriate response models
@app.get("/vd18_ids/")
async def get_vd18_ids(start: Optional[int] = None, end: Optional[int] = None):
    if start and end:
        return {"message":
                f"Dict of vd18 ids in index range {start}-{end}: {vd18_id_dict[start:end]}"
                }
    else:
        return {"message":
                f"Complete dict of vd18 ids: {vd18_id_dict}"
                }


@app.get("/vd18_ids/{vd18_id}")
async def get_vd18_id(vd18_id: str):
    if vd18_id in vd18_id_dict:
        return {"message": f"ID:{vd18_id} found!"}

    return {"message": f"{vd18_id} was not found!"}


@app.post("/vd18_ids/")
async def post_vd18_id(vd18_id: str, vd18_url: str):
    if vd18_id not in vd18_id_dict:
        vd18_id_dict[vd18_id] = vd18_url

        # Send the posted vd18_id inside the priority queue
        producer.basic_publish(f"{vd18_id}, {vd18_id_dict[vd18_id]}".encode('utf8'))

        return {"message": f"{vd18_id} is posted!"}
    else:
        return {"message": f"{vd18_id} was already posted!"}


def main():
    uvicorn.run(app, host=SERVER_IP, port=SERVER_PORT)


if __name__ == "__main__":
    main()
