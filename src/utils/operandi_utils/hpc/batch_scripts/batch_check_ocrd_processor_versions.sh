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

SIFS_DIR_PATH="/mnt/lustre-emmy-hdd/projects/project_pwieder_ocr_nhr/ocrd_processor_sifs"

if [ ! -d "${SIFS_DIR_PATH}" ]; then
  echo "Required sifs directory not found at: ${SIFS_DIR_PATH}"
  exit 1
fi

echo -n "Starting checking versions of ocr-d processors"

processor_image="ocrd_core.sif"
ocrd_processors=("ocrd" "ocrd-dummy")
echo -n "$processor_image"
for ocrd_processor in "${ocrd_processors[@]}"
do
  echo ""
  echo "$ocrd_processor " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "$ocrd_processor" --version || true
  echo ""
done
echo $'\n'


processor_image="ocrd_calamari.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-calamari-recognize" --version || true
echo $'\n'

processor_image="ocrd_olena.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-olena-binarize" --version || true
echo $'\n'

processor_image="ocrd_dinglehopper.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-dinglehopper" --version || true
echo $'\n'

processor_image="ocrd_eynollah.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-eynollah-segment" --version || true
echo $'\n'

processor_image="ocrd_fileformat.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-fileformat-transform" --version || true
echo $'\n'

processor_image="ocrd_nmalign.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-nmalign-merge" --version || true
echo $'\n'

processor_image="ocrd_sbb_binarization.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-sbb-binarize" --version || true
echo $'\n'

processor_image="ocrd_detectron2.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-detectron2-segment" --version || true
echo $'\n'

processor_image="ocrd_froc.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-froc-recognize" --version || true
echo $'\n'

processor_image="ocrd_pagetopdf.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-pagetopdf" --version || true
echo $'\n'

processor_image="ocrd_keraslm.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-keraslm-rate" --version || true
echo $'\n'

processor_image="ocrd_docstruct.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-docstruct" --version || true
echo $'\n'

processor_image="ocrd_doxa.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-doxa-binarize" --version || true
echo $'\n'

processor_image="ocrd_im6convert.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-im6convert" --version || true
echo $'\n'

processor_image="ocrd_olahd-client.sif"
echo "$processor_image " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "ocrd-olahd-client" --version || true
echo $'\n'


processor_image="ocrd_tesserocr.sif"
ocrd_processors=(
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
echo -n "$processor_image"
for ocrd_processor in "${ocrd_processors[@]}"
do
  echo ""
  echo "$ocrd_processor " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "$ocrd_processor" --version || true
  echo ""
done
echo $'\n\n'

apptainer exec "${SIFS_DIR_PATH}/$processor_image" ocrd-tesserocr-recognize --dump-module-dir || true
apptainer exec "${SIFS_DIR_PATH}/$processor_image" ls -la /models || true
echo $'\n\n'


processor_image="ocrd_anybaseocr.sif"
ocrd_processors=(
"ocrd-anybaseocr-binarize"
"ocrd-anybaseocr-block-segmentation"
"ocrd-anybaseocr-crop"
"ocrd-anybaseocr-deskew"
"ocrd-anybaseocr-dewarp"
"ocrd-anybaseocr-layout-analysis"
"ocrd-anybaseocr-textline"
"ocrd-anybaseocr-tiseg"
)
echo -n "$processor_image"
for ocrd_processor in "${ocrd_processors[@]}"
do
  echo ""
  echo "$ocrd_processor " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "$ocrd_processor" --version || true
  echo ""
done
echo $'\n\n'


processor_image="ocrd_cis.sif"
ocrd_processors=(
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
)
echo -n "$processor_image"
for ocrd_processor in "${ocrd_processors[@]}"
do
  echo ""
  echo "$ocrd_processor " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "$ocrd_processor" --version || true
  echo ""
done
echo $'\n\n'


processor_image="ocrd_cor-asv-ann.sif"
ocrd_processors=(
"ocrd-cor-asv-ann-align"
"ocrd-cor-asv-ann-evaluate"
"ocrd-cor-asv-ann-join"
"ocrd-cor-asv-ann-mark"
"ocrd-cor-asv-ann-process"
)
echo -n "$processor_image"
for ocrd_processor in "${ocrd_processors[@]}"
do
  echo ""
  echo "$ocrd_processor " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "$ocrd_processor" --version || true
  echo ""
done
echo $'\n\n'


processor_image="ocrd_segment.sif"
ocrd_processors=(
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
)
echo -n "$processor_image"
for ocrd_processor in "${ocrd_processors[@]}"
do
  echo ""
  echo "$ocrd_processor " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "$ocrd_processor" --version || true
  echo ""
done
echo $'\n\n'


processor_image="ocrd_kraken.sif"
ocrd_processors=("ocrd-kraken-binarize" "ocrd-kraken-recognize" "ocrd-kraken-segment")
echo -n "$processor_image"
for ocrd_processor in "${ocrd_processors[@]}"
do
  echo ""
  echo "$ocrd_processor " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "$ocrd_processor" --version || true
  echo ""
done
echo $'\n\n'


processor_image="ocrd_wrap.sif"
ocrd_processors=(
"ocrd-preprocess-image"
"ocrd-skimage-binarize"
"ocrd-skimage-denoise"
"ocrd-skimage-denoise-raw"
"ocrd-skimage-normalize"
)
echo -n "$processor_image"
for ocrd_processor in "${ocrd_processors[@]}"
do
  echo ""
  echo "$ocrd_processor " & apptainer exec "${SIFS_DIR_PATH}/$processor_image" "$ocrd_processor" --version || true
  echo ""
done
echo $'\n\n'
