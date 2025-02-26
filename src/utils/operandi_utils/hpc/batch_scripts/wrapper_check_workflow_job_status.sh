#!/bin/bash

# $0 - This bash script
# $1 - Slurm job id

sacct -j "$1" --format=jobid%-20,state%-20,exitcode
