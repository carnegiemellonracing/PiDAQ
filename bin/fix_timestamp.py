import csv
import datetime
import os
import sys

def convert_timestamps_in_csv(filename):
    # Generate the output filename with 'S-' prefix
    base_name = os.path.basename(filename)
    output_filename = f"S-{base_name}"

    # Open the input and output CSV files simultaneously
    with open(filename, 'r', newline='', encoding='utf-8') as csvfile_in, \
         open(output_filename, 'w', newline='', encoding='utf-8') as csvfile_out:
        reader = csv.reader(csvfile_in)
        writer = csv.writer(csvfile_out)

        # Read and write the header row
        header = next(reader)
        writer.writerow(header)

        # Process each row one at a time
        for row in reader:
            if row:  # Ensure the row is not empty
                try:
                    # Convert the timestamp in the first column
                    timestamp = float(row[0])
                    dt = datetime.datetime.fromtimestamp(timestamp)
                    iso_time = dt.isoformat()
                    row[0] = iso_time
                except ValueError:
                    print(f"Skipping row with invalid timestamp: {row}")
                # Write the modified row to the output file
                writer.writerow(row)
    print(f"Converted file saved as {output_filename}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_csv_timestamps.py <filename>")
    else:
        filename = sys.argv[1]
        convert_timestamps_in_csv(filename)
