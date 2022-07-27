#!/bin/bash -ue
docker run --rm -v null:/data -w /data -- ocrd/all:maximum ocrd workspace find --file-grp DEFAULT --download --wait 1
