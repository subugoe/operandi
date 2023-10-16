#!/bin/bash

SCRIPT_NAME=$(basename $0)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

ZIP_LINK="https://ocr-d-repo.scc.kit.edu/api/v1/dataresources/b22282d5-a206-4def-9021-7302199f7326/data/mangoldt_unternehmergewinn_1855.ocrd.zip"
ZIP_PATH="$SCRIPT_DIR/mangoldt_unternehmergewinn_1855.ocrd.zip"


if [ ! -e $ZIP_PATH ]; then
   wget $ZIP_LINK -P $SCRIPT_DIR
fi

unzip $ZIP_PATH -d $SCRIPT_DIR/temp

# Copy the OCR-D-IMG folder inside an ocrd-workspace folder
mkdir -p $SCRIPT_DIR/ocrd-workspace/OCR-D-IMG
cp -r $SCRIPT_DIR/temp/data/OCR-D-IMG/* $SCRIPT_DIR/ocrd-workspace/OCR-D-IMG

# Give all permisions
chmod -Rf 777 $SCRIPT_DIR/ocrd-workspace/OCR-D-IMG

rm -rf $SCRIPT_DIR/temp

# ocrd software must be installed beforehand, otherwise the following lines will not execute
# for the sake of script simplicity checks whether the software is installed or not are not done here!

# Based on https://ocr-d.de/en/user_guide#non-existing-mets
#ocrd workspace -d $SCRIPT_DIR/ocrd-workspace init
#ocrd workspace -d $SCRIPT_DIR/ocrd-workspace set-id "test_for_workflows"

#FILEGRP="OCR-D-IMG"
#EXT=".jpg"  # the actual extension of the image files
#MEDIATYPE="image/jpeg"  # the actual media type of the image files

#cd $SCRIPT_DIR/ocrd-workspace

#for i in $SCRIPT_DIR/ocrd-workspace/OCR-D-IMG/*$EXT; do
#  base=`basename ${i} $EXT`; # base holds OCR-D-IMG_*
#  base_num=${base##*_}; # base holds *
#  ocrd workspace add -G $FILEGRP -i ${FILEGRP}_${base_num} -g P_${base_num} -m $MEDIATYPE ${i};
#done

# Alternatively, executing the following script does the job! 
cd $SCRIPT_DIR/ocrd-workspace
/bin/bash $SCRIPT_DIR/ocrd-import.sh
