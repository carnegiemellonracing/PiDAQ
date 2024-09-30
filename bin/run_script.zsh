#!/bin/zsh

# Directory containing the CSV files
DIRECTORY="../rasppi/tests/remote"

# Iterate over each CSV file in the directory
for file in "$DIRECTORY"/*.csv; do
    # Check if the file exists
    if [ -f "$file" ]; then
        echo "Processing $file..."
        python3 videolize_temp_data.py "$file"
    fi
done

