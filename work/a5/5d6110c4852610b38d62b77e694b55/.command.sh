#!/bin/bash -ue
docker run --rm -v /home/mm/.local/lib/python3.8/site-packages/service_broker/nextflow_workspaces_local/PPN631277528/bin/ocrd-workspace:/data -w /data -- ocrd/all:maximum ocrd-cis-ocropy-binarize -m mets.xml -I DEFAULT -O "OCR-D-BIN"
