#!/bin/bash -ue
singularity exec --bind null docker://ocrd/all:maximum ocrd workspace find --file-grp DEFAULT --download --wait 1
