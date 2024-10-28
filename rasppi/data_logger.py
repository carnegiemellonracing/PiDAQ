import mqtt as mqtt_client
import csv_logger
import time
import json
import os

DAQ_PI_ID = os.getenv("DAQ_PI_ID")

current_test_name = None

def log_data(name, value, timestamp=time.time(), mqtt=True, csv=True):
    global current_test_name
    """Log data to MQTT and CSV files."""

    value = json.dumps(value)

    if mqtt:
        mqtt_client.send_data({
            "id": DAQ_PI_ID,
            "name": name,
            "value": value,
            "timestamp": timestamp,
            "testName": current_test_name
        })
    if csv:
        csv_logger.log_data(timestamp=timestamp, name=name, value=value)

def log_test_start(test_name, timestamp):
    global current_test_name
    current_test_name = test_name
    csv_logger.open_new_file(test_name, timestamp)
