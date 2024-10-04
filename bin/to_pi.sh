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

# Your rsync command
rsync -avz --exclude-from='.gitignore' --exclude 'node_modules' --exclude 'rasppi/tests' --exclude '.git' --exclude 'videos' . cmr@$HOSTNAME:~/24e-DAQ-v2-Website
