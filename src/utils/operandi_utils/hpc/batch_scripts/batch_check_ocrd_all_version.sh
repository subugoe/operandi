#!/bin/bash
#SBATCH --partition standard96:shared
#SBATCH --time 00:20:00
#SBATCH --qos 2h
#SBATCH --output check_ocrd_all_version_job-%J.txt
#SBATCH --cpus-per-task 1
#SBATCH --mem 16G

set -e

hostname
# /opt/slurm/etc/scripts/misc/slurm_resources

module purge
module load apptainer
SIF_PATH="/mnt/lustre-emmy-hdd/projects/project_pwieder_ocr_nhr/ocrd_processor_sifs/ocrd_all_maximum_image.sif"

apptainer exec "$SIF_PATH" ocrd-tesserocr-recognize --dump-module-dir
apptainer exec "$SIF_PATH" ls -la /models

ocrd_processors=(
"ocrd-anybaseocr-binarize"
"ocrd-anybaseocr-block-segmentation"
"ocrd-anybaseocr-crop"
"ocrd-anybaseocr-deskew"
"ocrd-anybaseocr-dewarp"
"ocrd-anybaseocr-layout-analysis"
"ocrd-anybaseocr-textline"
"ocrd-anybaseocr-tiseg"
"ocrd-calamari-recognize"
"ocrd-cis-align"
"ocrd-cis-data"
"ocrd-cis-ocropy-binarize"
"ocrd-cis-ocropy-clip"
"ocrd-cis-ocropy-denoise"
"ocrd-cis-ocropy-deskew"
"ocrd-cis-ocropy-dewarp"
"ocrd-cis-ocropy-recognize"
"ocrd-cis-ocropy-resegment"
"ocrd-cis-ocropy-segment"
"ocrd-cis-ocropy-train"
"ocrd-cis-postcorrect"
"ocrd-cor-asv-ann-align"
"ocrd-cor-asv-ann-evaluate"
"ocrd-cor-asv-ann-join"
"ocrd-cor-asv-ann-mark"
"ocrd-cor-asv-ann-process"
"ocrd-detectron2-segment"
"ocrd-dinglehopper"
"ocrd-docstruct"
"ocrd-doxa-binarize"
"ocrd-dummy"
"ocrd-eynollah-segment"
"ocrd-fileformat-transform"
"ocrd-froc-recognize"
"ocrd-im6convert"
"ocrd-import"
"ocrd-keraslm-rate"
"ocrd-kraken-binarize"
"ocrd-kraken-recognize"
"ocrd-kraken-segment"
"ocrd-make"
"ocrd-nmalign-merge"
"ocrd-olahd-client"
"ocrd-olena-binarize"
"ocrd-page2alto-transform"
"ocrd-pagetopdf"
"ocrd-page-transform"
"ocrd-preprocess-image"
"ocrd-repair-inconsistencies"
"ocrd-sbb-binarize"
"ocrd-segment-evaluate"
"ocrd-segment-extract-glyphs"
"ocrd-segment-extract-lines"
"ocrd-segment-extract-pages"
"ocrd-segment-extract-regions"
"ocrd-segment-extract-words"
"ocrd-segment-from-coco"
"ocrd-segment-from-masks"
"ocrd-segment-project"
"ocrd-segment-repair"
"ocrd-segment-replace-original"
"ocrd-segment-replace-page"
"ocrd-segment-replace-text"
"ocrd-skimage-binarize"
"ocrd-skimage-denoise"
"ocrd-skimage-denoise-raw"
"ocrd-skimage-normalize"
"ocrd-tesserocr-binarize"
"ocrd-tesserocr-crop"
"ocrd-tesserocr-deskew"
"ocrd-tesserocr-fontshape"
"ocrd-tesserocr-recognize"
"ocrd-tesserocr-segment"
"ocrd-tesserocr-segment-line"
"ocrd-tesserocr-segment-region"
"ocrd-tesserocr-segment-table"
"ocrd-tesserocr-segment-word"
)

for ocrd_processor in "${ocrd_processors[@]}"
do
  echo -n "$ocrd_processor " & apptainer exec "$SIF_PATH" "$ocrd_processor" --version || true
done
