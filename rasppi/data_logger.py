import mqtt as mqtt_client
import csv_logger
import datetime
import json
import os

import msgpack
import struct
import zlib

DAQ_PI_ID = os.getenv("DAQ_PI_ID")
STRING_BYTE_LIMIT = 46

current_test_name = None

def log_data(name, value, timestamp=None, mqtt=True, csv=True):
    global current_test_name
    """Log data to MQTT and CSV files."""

    if timestamp is None:
        timestamp = datetime.datetime.utcnow().isoformat()

    # value = json.dumps(value)

    if mqtt:
        payload = get_payload(DAQ_PI_ID,current_test_name,timestamp, name, value)
        mqtt_client.send_data(payload)

    if csv:
        csv_logger.log_data(timestamp=timestamp, name=name, value=value)

def log_test_start(test_name, timestamp):
    global current_test_name
    current_test_name = test_name
    csv_logger.open_new_file(test_name, timestamp)

def get_payload(pi_id, current_test_name, timestamp, data_label, value):
    pi_id = limit_string_length(pi_id, STRING_BYTE_LIMIT)
    current_test_name = limit_string_length(current_test_name, STRING_BYTE_LIMIT)
    data_label = limit_string_length(data_label, STRING_BYTE_LIMIT)
    timestamp = limit_string_length(timestamp, STRING_BYTE_LIMIT)

    fixed_part = struct.pack(f"{STRING_BYTE_LIMIT}s"*4,pi_id.encode(),current_test_name.encode(), data_label.encode(), timestamp.encode())
    variable_part = msgpack.packb(value)

    payload = fixed_part + variable_part
    compressed_payload = zlib.compress(payload)

    return compressed_payload


def limit_string_length(string, length):
    return str(string).ljust(length)[:length]
