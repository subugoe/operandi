#!/bin/bash
#SBATCH --partition standard96:shared
#SBATCH --time 4:00:00
#SBATCH --output create_ocrd_slim_sif_images_job-%J.txt
#SBATCH --cpus-per-task 16
#SBATCH --mem 64G

set -e

module purge
module load apptainer

hostname
# /opt/slurm/etc/scripts/misc/slurm_resources

APPTAINER_TMPDIR="$LOCAL_TMPDIR"
APPTAINER_CACHE_DIR="/mnt/lustre-emmy-hdd/projects/project_pwieder_ocr_nhr/ocrd_processor_sifs_tmp"

if [ ! -d "${APPTAINER_CACHE_DIR}" ]; then
  echo "Creating non-existing APPTAINER_CACHE_DIR folder"
  mkdir -p "${APPTAINER_CACHE_DIR}"
fi

cd "${APPTAINER_CACHE_DIR}" || exit

declare -a images=(
"core"
"tesserocr"
"cis"
"kraken"
"wrap"
"calamari"
"olena"
"dinglehopper"
"eynollah"
"fileformat"
"nmalign"
"segment"
"anybaseocr"
"sbb_binarization"
"froc"
"pagetopdf"
"keraslm"
"docstruct"
"doxa"
"im6convert"
"olahd-client"
"detectron2"
"cor-asv-ann"
)

for image in "${images[@]}"
do
    if [ -f "$APPTAINER_CACHE_DIR/ocrd_$image.sif" ]; then
      echo "Already exists, skipping: $APPTAINER_CACHE_DIR/ocrd_$image.sif"
      continue
    fi
    echo "Building SIF of $image"
    apptainer build --disable-cache "ocrd_$image.sif" "docker://ocrd/$image:latest"
    case $? in
      0) echo "Building complete: $APPTAINER_CACHE_DIR/ocrd_$image.sif" ;;
      *) echo "Building failed, error code: $?" >&2 ;;
    esac
    echo ""
done
