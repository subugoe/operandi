#!/bin/bash

# $0 - The batch script path to execute
# $1 - Slurm parameter - partition
# $2 - Slurm parameter - time
# $3 - Slurm parameter - output
# $4 - Slurm parameter - cpus-per-task
# $5 - Slurm parameter - mem
# $6 - Slurm parameter - qos

# $7 - The scratch base for slurm workspaces
# $8 - Workflow job id
# $9 - Nextflow script id
# $10 - Entry input file group
# $11 - Workspace id
# $12 - Mets basename - default "mets.xml"
# $13 - CPUs for the Nextflow processes
# $14 - RAM for the Nextflow processes
# $15 - Amount of forks per OCR-D processor in the NF script
# $16 - Amount of pages in the workspace
# $17 - Boolean flag showing whether a mets server is utilized or not
# $18 - File groups to be removed from the workspace after the processing

sbatch "$0" --partition="$1" --time="$2" --output="$3" --cpus-per-task="$4" --mem="$5" --qos="$6" "$7" "$8" "$9" "${10}" "${11}" "${12}" "${13}" "${14}" "${15}" "${16}" "${17}" "${18}"
