#!/bin/bash -ue
docker run --rm -v null:/data -w /data -- ocrd/all:maximum ocrd-cis-ocropy-binarize -m mets.xml -I DEFAULT -O "OCR-D-BIN"
