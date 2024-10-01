#!/bin/bash
# Set the working directory to the location of the script
cd "$(dirname "$0")/.."

# Your rsync command
rsync -avz --exclude-from='.gitignore' --exclude 'node_modules' --exclude 'rasppi/tests' --exclude '.git' --exclude 'videos' . cmr@raspberrypi.local:~/24e-DAQ-v2-Website
