#!/bin/bash

# $0 - This bash script
# $1 - Slurm parameter - partition
# $2 - Slurm parameter - time
# $3 - Slurm parameter - output
# $4 - Slurm parameter - cpus-per-task
# $5 - Slurm parameter - mem
# $6 - Slurm parameter - qos

# $7 - The batch script path to execute
# $8 - The scratch base for slurm workspaces
# $9 - Workflow job id
# $10 - Nextflow script id
# $11 - Entry input file group
# $12 - Workspace id
# $13 - Mets basename - default "mets.xml"
# $14 - CPUs for the Nextflow processes
# $15 - RAM for the Nextflow processes
# $16 - Amount of forks per OCR-D processor in the NF script
# $17 - Amount of pages in the workspace
# $18 - Boolean flag showing whether a mets server is utilized or not
# $19 - File groups to be removed from the workspace after the processing

if [ "$6" == "48h" ] ; then
  # QOS not set, the default of 48h is used
  sbatch --partition="$1" --time="$2" --output="$3" --cpus-per-task="$4" --mem="$5" "$7" "$8" "$9" "${10}" "${11}" "${12}" "${13}" "${14}" "${15}" "${16}" "${17}" "${18}" "${19}"
else
  sbatch --partition="$1" --time="$2" --output="$3" --cpus-per-task="$4" --mem="$5" --qos="$6" "$7" "$8" "$9" "${10}" "${11}" "${12}" "${13}" "${14}" "${15}" "${16}" "${17}" "${18}" "${19}"
fi

echo "0:$0 1:$1 2:$2 3:$3 4:$4 5:$5 6:$6 7:$7 8:$8 9:$9 10:${10}"
echo "11:${11} 12:${12} 13:${13} 14:${14} 15:${15} 16:${16} 17:${17} 18:${18} 19:${19}"
