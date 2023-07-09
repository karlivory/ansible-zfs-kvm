#!/bin/bash

# This script is used to synchronize multiple ZFS datasets between source and destination hosts using Syncoid.
# It reads a configuration file called datasets.conf that defines the dataset pairs to be synced.
#
# The datasets.conf file should have the following format:
#   SRC_HOST:SRC_DATASET   DEST_HOST:DEST_DATASET
# e.g. user1@host1:pool1/dataset1   user2@host2:pool2/dataset2
# Each line represents a dataset pair to be synced. Lines starting with a "#" character and empty lines are ignored.
#
# syncoid is run on the source host via SSH with agent forwarding, so 
#   ssh user1@host1
#   ssh -A user1@host1 "ssh user2@host2"
# must work.
# The script outputs the sync progress for each dataset pair and exits with a helpful message if the datasets.conf file format is invalid.

# function to validate datasets.conf format
function validate_datasets_file() {
  local FILE=$1
  local LINE_NUM=0

  while read -r LINE; do
    LINE_NUM=$((LINE_NUM + 1))

    # Skip empty lines and comments
    if [[ "$LINE" =~ ^\s*$ ]] || [[ "$LINE" == \#* ]]; then
      continue
    fi

    # Validate format: user1@host1:pool1/dataset1   user2@host2:pool2/dataset2
    if ! [[ "$LINE" =~ ^[^@]+@[0-9a-zA-Z.]+:[^[:space:]]+\s+[^@]+@[0-9a-zA-Z.]+:[^[:space:]]+$ ]]; then
      echo "Invalid datasets.conf format at line $LINE_NUM: $LINE"
      echo "Expected format: user1@host1:pool1/dataset1   user2@host2:pool2/dataset2"
      exit 1
    fi
  done < "$FILE"
}
# Validate datasets file
DATASETS_FILE="datasets.conf"
validate_datasets_file "$DATASETS_FILE"

# Create an empty dict (associative array)
declare -A DATASETS

# Read the datasets from DATASETS_FILE to DATASETS dict
while read -r SRC_HOST_DATASET DEST_HOST_DATASET; do
  # Skip empty lines and comment lines
  if [[ "$SRC_HOST_DATASET" =~ ^\s*$ ]] || [[ "$SRC_HOST_DATASET" == \#* ]]; then
    continue
  fi
  DATASETS["$SRC_HOST_DATASET"]="$DEST_HOST_DATASET"
done < "$DATASETS_FILE"

echo "== $(date) start =="

# Loop through dataset pairs and run Syncoid for each
for SRC_HOST_DATASET in "${!DATASETS[@]}"; do
  DEST_HOST_DATASET="${DATASETS[$SRC_HOST_DATASET]}"
  echo "Syncing $SRC_HOST_DATASET to $DEST_HOST_DATASET"

  # Extract source host from SRC_HOST_DATASET
  SRC_HOST="${SRC_HOST_DATASET%%:*}"

  # Run syncoid command on the source host using ssh with agent forwarding (syncoid requires -t to work)
  ssh -At "$SRC_HOST" "/usr/sbin/syncoid -r --compress=lz4 --no-sync-snap '$SRC_HOST_DATASET' '$DEST_HOST_DATASET'"
done

echo "======================= done ========================="

