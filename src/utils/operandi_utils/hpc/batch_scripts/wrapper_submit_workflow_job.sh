#!/bin/bash

module purge
module load jq

sbatch_args="$1"
constraint=$(echo "$sbatch_args" | jq .constraint | tr -d '"')
partition=$(echo "$sbatch_args" | jq .partition | tr -d '"')
deadline_time=$(echo "$sbatch_args" | jq .job_deadline_time | tr -d '"')
output=$(echo "$sbatch_args" | jq .output_log | tr -d '"')
cpus_per_task=$(echo "$sbatch_args" | jq .cpus | tr -d '"')
memory=$(echo "$sbatch_args" | jq .ram | tr -d '"')
qos=$(echo "$sbatch_args" | jq .qos | tr -d '"')
batch_script_path=$(echo "$sbatch_args" | jq .batch_script_path | tr -d '"')

# $2 is a json of regular arguments used inside the `batch_submit_workflow_job.sh`
if [ "$qos" == "48h" ] ; then
  # QOS not set, the default of 48h is used
  sbatch --constraint="$constraint" --partition="$partition" --time="$deadline_time" --output="$output" --cpus-per-task="$cpus_per_task" --mem="$memory" "$batch_script_path" "$2"
else
  sbatch --constraint="$constraint" --partition="$partition" --time="$deadline_time" --output="$output" --cpus-per-task="$cpus_per_task" --mem="$memory" --qos="$qos" "$batch_script_path" "$2"
fi

echo "executed wrapper script: $0"
echo "constraint: $constraint"
echo "partition: $partition"
echo "deadline_time: $deadline_time"
echo "output: $output"
echo "cpus_per_task: $cpus_per_task"
echo "memory: $memory"
echo "qos: $qos"
echo "batch_script_path: $batch_script_path"
echo "regular_args: $2"
