#!/bin/bash

SCRIPT_NAME=$(basename $0)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

ZIP_LINK="https://ocr-d-repo.scc.kit.edu/api/v1/dataresources/b22282d5-a206-4def-9021-7302199f7326/data/mangoldt_unternehmergewinn_1855.ocrd.zip"
ZIP_PATH="$SCRIPT_DIR/mangoldt_unternehmergewinn_1855.ocrd.zip"


if [ ! -e $ZIP_PATH ]; then
   wget $ZIP_LINK -P $SCRIPT_DIR
fi

unzip $ZIP_PATH -d $SCRIPT_DIR/temp

FILEGRP="OCR-D-IMG" # The file group
EXT=".jpg"  # the actual extension of the image files
MEDIATYPE="image/jpeg"  # the actual media type of the image files

# Divide the workspace to 4 equal parts
for i in {1..4}; do
   mkdir -p $SCRIPT_DIR/ocrd-workspace/sub-workspace-${i}/OCR-D-IMG
   cp $SCRIPT_DIR/temp/data/OCR-D-IMG/OCR-D-IMG_000${i}.jpg $SCRIPT_DIR/ocrd-workspace/sub-workspace-${i}/OCR-D-IMG/
   cp $SCRIPT_DIR/temp/data/OCR-D-IMG/OCR-D-IMG_000$((i+4)).jpg $SCRIPT_DIR/ocrd-workspace/sub-workspace-${i}/OCR-D-IMG/
   
   #ocrd workspace -d $SCRIPT_DIR/ocrd-workspace/sub-workspace-${i} init
   #ocrd workspace -d $SCRIPT_DIR/ocrd-workspace/sub-workspace-${i} set-id "parallel_workflow"
   
   #cd $SCRIPT_DIR/ocrd-workspace/sub-workspace-${i}
   
   #for x in $SCRIPT_DIR/ocrd-workspace/sub-workspace-${i}/OCR-D-IMG/*$EXT; do
   #  base=`basename ${x} $EXT`; # base holds OCR-D-IMG_*
   #  base_num=${base##*_}; # base holds *
   #  ocrd workspace add -G $FILEGRP -i ${FILEGRP}_${base_num} -g P_${base_num} -m $MEDIATYPE ${i};
   #done
   
   #cd $SCRIPT_DIR/ocrd-workspace
   
   /bin/bash $SCRIPT_DIR/ocrd-import.sh $SCRIPT_DIR/ocrd-workspace/sub-workspace-${i}
   # The script does not work properly to divide the workspace!
done

rm -rf $SCRIPT_DIR/temp

# Give all permisions
chmod -Rf 777 $SCRIPT_DIR/ocrd-workspace/*
