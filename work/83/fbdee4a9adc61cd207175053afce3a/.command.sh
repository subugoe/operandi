#!/bin/bash -ue
docker run --rm -v /home/mm/.local/lib/python3.8/site-packages/service_broker/nextflow_workspaces_local/PPN631277528/bin/ocrd-workspace:/bin -w /bin -- ocrd/all:maximum ocrd workspace find --file-grp DEFAULT --download --wait 1
