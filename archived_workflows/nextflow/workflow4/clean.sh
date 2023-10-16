#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

rm -rf $SCRIPT_DIR/ocrd-workspace
rm -rf $SCRIPT_DIR/input
rm -rf $SCRIPT_DIR/output
rm -rf $SCRIPT_DIR/work
rm -rf $SCRIPT_DIR/temp
rm -rf $SCRIPT_DIR/.nextflow
rm -f $SCRIPT_DIR/.nextflow.log*
#rm -f $SCRIPT_DIR/mangoldt_unternehmergewinn_1855.ocrd.zip
rm -f report.*
