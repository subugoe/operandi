#!/bin/bash
#SBATCH --constraint scratch
#SBATCH --partition medium
#SBATCH --cpus-per-task 2
#SBATCH --mem 32G
#SBATCH --output /home/users/mmustaf/jobs_output/job-%J.txt

# The username above is set to static again. When the user name is
# passed as an option parameter it complicates things. The submitted 
# batch script has to be wrapped by another batch script. 
# In the end, two job IDs are created instead of one.

# "$1" is the first parameter to this script -> the workspace name

hostname
slurm_resources

# clear the environment then load singularity and nextflow
module purge
module load singularity # loads "git" and "go" as well
module load nextflow # loads "openjdk" as well

# Check if scratch contains username folder
# If not, create it
if [ ! -d "/scratch1/users/${USER}" ]; then
  mkdir "/scratch1/users/${USER}"
fi

# Create a workspace directory under the USER with name METS ID
mkdir "/scratch1/users/${USER}/$1"

# Check if created
if [ ! -d "/scratch1/users/${USER}/$1" ]; then
  echo "Workspace directory was not created!"
  exit 1
fi

# copies the ocrd-workspace folder which holds the OCR-D-IMG folder and the mets file
# copies the Nextflow script - seq_ocrd_wf_single_processor.nf

# Copy the workspace from home to scratch
cp -rf "/home/users/${USER}/$1/bin" "/scratch1/users/${USER}/$1"
# Delete the workspace from home
rm -rf "/home/users/${USER}/$1"
cd "/scratch1/users/${USER}/$1/bin" || exit

# TODO: Here should the images from the METS file downloaded
# With the help of the "ocrd workspace" functionality
echo "DOWNLOADING THE IMAGES FROM METS FILE ... DUMMY"

# execute the main Nextflow script
nextflow run seq_ocrd_wf_single_processor.nf --volumedir "/scratch1/users/${USER}/$1/bin"

# Delete the results from the scratch
# rm -rf "/scratch1/users/${USER}/$1"
