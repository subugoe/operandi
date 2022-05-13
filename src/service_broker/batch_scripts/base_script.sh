#!/bin/bash
sbatch <<EOT
#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 4
#SBATCH --mem 16G
#SBATCH --output "$1"/jobs_output/job-%J.txt

# "$1" is the first parameter to this script -> ${USER}'s home directory

echo "$1 and $2"

# clear the environment then load singularity and nextflow
module purge
module load singularity # loads "git" and "go" as well
module load nextflow # loads "openjdk" as well

# Check if scratch contains username folder
# If not, create it
if [ ! -d "/scratch1/users/${USER}" ]; then
  mkdir "/scratch1/users/${USER}"
fi

# Create a temporary directory with a random name
mkdir "/scratch1/users/${USER}/$2"

# Check if created
if [ ! -d "/scratch1/users/${USER}/$2" ]; then
  echo "Temp directory was not created!"
  exit 1
fi

# copies the ocrd-workspace folder which holds the OCR-D-IMG folder and the mets file
# copies the Nextflow script - seq_ocrd_wf_single_processor.nf

# "$2" is the second parameter to this script -> the workspace name
cp -rf /home/users/"${USER}"/"$2"/bin "/scratch1/users/${USER}/$2"

cd /scratch1/users/${USER}/$2/bin || exit

# TODO: Here should the images from the METS file downloaded
# With the help of the "ocrd workspace" functionality
echo "DOWNLOADING THE IMAGES FROM METS FILE ... DUMMY"

# execute the main Nextflow script
nextflow run seq_ocrd_wf_single_processor.nf --tempdir "/scratch1/users/${USER}/$2/bin"

hostname
slurm_resources

# rm -rf "/scratch1/users/${USER}/$2"

EOT
