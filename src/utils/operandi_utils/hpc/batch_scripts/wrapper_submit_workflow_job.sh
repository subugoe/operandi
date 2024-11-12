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

module purge
module load jq

sbatch_args="$1"
partition=$(echo "$sbatch_args" | jq .partition | tr -d '"')
deadline_time=$(echo "$sbatch_args" | jq .job_deadline_time | tr -d '"')
output=$(echo "$sbatch_args" | jq .output_log | tr -d '"')
cpus_per_task=$(echo "$sbatch_args" | jq .cpus | tr -d '"')
memory=$(echo "$sbatch_args" | jq .ram | tr -d '"')
qos=$(echo "$sbatch_args" | jq .qos | tr -d '"')
batch_script_path=$(echo "$sbatch_args" | jq .batch_script_path | tr -d '"')

if [ "$qos" == "48h" ] ; then
  # QOS not set, the default of 48h is used
  sbatch --partition="$partition" --time="$deadline_time" --output="$output" --cpus-per-task="$cpus_per_task" --mem="$memory" "$batch_script_path" "$2"
else
  sbatch --partition="$partition" --time="$deadline_time" --output="$output" --cpus-per-task="$cpus_per_task" --mem="$memory" --qos="$qos" "$batch_script_path" "$2"
fi

echo "executed wrapper script: $0"
echo "partition: $partition"
echo "deadline_time: $deadline_time"
echo "output: $output"
echo "cpus_per_task: $cpus_per_task"
echo "memory: $memory"
echo "qos: $qos"
echo "batch_script_path: $batch_script_path"
