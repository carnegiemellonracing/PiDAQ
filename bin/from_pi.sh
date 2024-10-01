#!/bin/bash
# Set the working directory to the location of the script
cd "$(dirname "$0")/.."

# Rsync command
rsync -avz \
  cmr@raspberrypi.local:~/24e-DAQ-v2-Website/rasppi/tests rasppi
