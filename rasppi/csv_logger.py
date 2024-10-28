import threading
import csv
import time
import os
from logger import log

csv_writer = None  # CSV writer object
data_file = None  # File object
last_test_name = None

csv_file_lock = threading.Lock()
CSV_HEADER = "timestamp,name,value\n"
DAQ_PI_ID = os.getenv("DAQ_PI_ID")

def get_file_name(test_name, timestamp):
    """Generate a unique file name for each test."""
    directory = f"tests/{timestamp.strftime('%Y_%m_%d')}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    return f"{directory}/{timestamp.strftime('%H_%M')}_{test_name}_PI{DAQ_PI_ID}.csv"

def open_new_file(test_name, timestamp):
    with csv_file_lock:
        """Open a new CSV file and create a CSV writer object."""
        global data_file, csv_writer, last_test_name
        if data_file:
            data_file.close()  # Close the old file if it exists

        file_name = get_file_name(
            test_name=test_name, timestamp=timestamp
        )

        data_file = open(file_name, mode="w", newline="")
        csv_writer = csv.writer(data_file)
        csv_writer.writerow(["timestamp", "tire_temp_frame", "linpot", "ride_height"])
        last_test_name = test_name

        log(f"Opened new file: {file_name}")


def log_data(name, value, timestamp):
    """Write sensor data to the CSV file."""
    with csv_file_lock:
        if csv_writer:
            csv_writer.writerow(
                [
                    timestamp, name, value
                ]
            )
            data_file.flush()  # Ensure data is written to disk
