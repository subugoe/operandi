#!/bin/bash

SCRIPT_NAME=$(basename $0)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

mkdir -p input_folder
mkdir -p step1_out
mkdir -p step2_out
mkdir -p step3_out

