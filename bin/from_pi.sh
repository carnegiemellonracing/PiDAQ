#!/bin/bash

# Check if hostname is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <hostname>"
  exit 1
fi

# Set the hostname from the first argument
HOSTNAME=$1

# Set the working directory to the location of the script
cd "$(dirname "$0")/.."

# Rsync command
rsync -avz \
  cmr@"$HOSTNAME":~/24e-DAQ-v2-Website/rasppi/tests rasppi
