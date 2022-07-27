#!/bin/bash -ue
singularity exec --bind null docker://ocrd/all:maximum ocrd-cis-ocropy-binarize -m mets.xml -I DEFAULT -O "OCR-D-BIN"
