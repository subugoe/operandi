#!/bin/bash

SCRIPT_NAME=$(basename $0)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

METS_LINK="https://content.staatsbibliothek-berlin.de/dc/PPN631277528.mets.xml"
METS_PATH="$SCRIPT_DIR/ocrd-workspace/mets.xml"

if [ ! -e $SCRIPT_DIR/ocrd-workspace ]; then
  mkdir $SCRIPT_DIR/ocrd-workspace
fi

if [ ! -e $METS_PATH ]; then
  wget $METS_LINK -P $SCRIPT_DIR
  mv $SCRIPT_DIR/*mets.xml $SCRIPT_DIR/ocrd-workspace/mets.xml
fi

cd $SCRIPT_DIR/ocrd-workspace
ocrd workspace find --file-grp DEFAULT --download

