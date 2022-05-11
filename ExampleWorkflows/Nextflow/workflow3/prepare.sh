#!/bin/bash

SCRIPT_NAME=$(basename $0)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

ZIP_LINK="https://ocr-d-repo.scc.kit.edu/api/v1/dataresources/736a2f9a-92c6-4fe3-a457-edfa3eab1fe3/data/wundt_grundriss_1896.ocrd.zip"
ZIP_PATH="$SCRIPT_DIR/wundt_grundriss_1896.ocrd.zip"

if [ ! -e $ZIP_PATH ]; then
   wget $ZIP_LINK -P $SCRIPT_DIR
fi

unzip $ZIP_PATH -d $SCRIPT_DIR/temp

for i in {1..3}
do
   mkdir -p $SCRIPT_DIR/input/workspaces$i
   cp -r $SCRIPT_DIR/temp/* $SCRIPT_DIR/input/workspaces$i
done

rm -r $SCRIPT_DIR/temp
