import os
import random

DAQ_PI_ID = os.getenv("DAQ_PI_ID") or f"RPI-{random.randint(1000, 9999)}"
os.environ["DAQ_PI_ID"] = DAQ_PI_ID

import time
import argparse
import json
import datetime
import data_logger
import csv_logger
import threading
import base64

from logger import log, log_to_file
import mqtt

# toggle sensors
DISCONNECT_TIMEOUT_SECONDS = 300

connected = False

# Get Pi ID from environment or set randomly in test mode
# Global sensor objects (initialized once in main())
sensors = {}

# Command-line argument parsing
parser = argparse.ArgumentParser(description="Process CLI arguments.")
parser.add_argument("ip_address", type=str, help="IP address of the MQTT Broker")
parser.add_argument("-t", "--test_mode", action="store_true", help="Run in test mode")
parser.add_argument("-a", "--adc", action="store_true", help="Enable ADC sensor")
parser.add_argument("-m", "--mlx", action="store_true", help="Enable MLX90640 sensor")
parser.add_argument("-v", "--vl", action="store_true", help="Enable VL53L0X sensor")
parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")

args = parser.parse_args()
is_test_mode = args.test_mode
adc_active = args.adc
mlx_active = args.mlx
vl53l0x_active = args.vl
debug_mode = args.debug

if not debug_mode:
    log_to_file("program.log")

# Setting the client ID for this RPi

if DAQ_PI_ID is None:
    if is_test_mode:
        log("WARNING: DAQ_PI_ID not set in environment. Using random value")
        DAQ_PI_ID = random.randint(1, 100)
    else:
        log("ERROR: DAQ_PI_ID not set in environment.")
        exit(1)

# Conditionally importing libraries

if is_test_mode:
    log("Running in dry run test mode.")
else:
    log("Running in normal mode.")
    import board
    import busio
    from sensors.max11617 import init_max11617, read_adc
    from sensors.vl53l0x import init_vl53l0x, read_range
    from sensors.mlx90640 import init_mlx90640, read_frame

class TestingState:
    def __init__(self):
        self.test_state = False
        self.test_time_stamp = None
        self.test_name = ""
        self.dry_run = bool(is_test_mode)
        self.daq_pi_id = (
            DAQ_PI_ID if DAQ_PI_ID is not None else random.randint(1000, 9999)
        )

        if self.daq_pi_id is None:
            log(
                "WARNING: Raspberry Pi ID could not be read from system. Setting a random ID for testing purposes."
            )

    def get_name(self):
        return self.test_name

    def set_name(self, test_name):
        self.test_name = test_name

    def get_state(self):
        return self.test_state

    def set_state(self, test_state):
        self.test_state = test_state

    def get_timestamp(self):
        return self.test_time_stamp

    def start_test(self, test_name, timestamp):
        self.test_name = test_name
        self.test_time_stamp = timestamp
        self.test_state = True

    def stop_test(self):
        self.test_state = False
        self.test_name = ""
        self.test_timestamp = None

testStateManager = TestingState()

def handle_message(data):
    test_name = data["test_name"]
    if data["command"] == "start":
        testStateManager.start_test(test_name, datetime.datetime.now())
        data_logger.log_test_start(test_name, testStateManager.get_timestamp())
        log(f'Started test: "{test_name}"')
    elif data["command"] == "stop":
        testStateManager.stop_test()
        log(f'Stopped test: "{test_name}"')

def compute_average_temp(data_frame):
    """Compute the average temperature from the MLX90640 data frame."""
    data_frame = [float(temp) for temp in data_frame]
    if len(data_frame) != 768:
        raise ValueError("Data frame must contain exactly 768 temperature values.")

    return int((sum(data_frame) / len(data_frame)))

# Thread to collect sensor data and place it in the MQTT queue.
def read_sensors():

    last_full_frame = None
    while True:
        if not testStateManager.test_state:
            time.sleep(1)  # Avoid busy waiting
            continue

        if not testStateManager.get_state():
            continue

        if not is_test_mode:
            # Collect real sensor data using pre-initialized sensors


            if mlx_active:
                try :
                    mlx = sensors.get("mlx")
                    mlx_data_frame= read_frame(mlx)

                    send_mqtt =not last_full_frame or  (time.time() - last_full_frame) > 1
                    data_logger.log_data(name="tire_temp_frame", value=mlx_data_frame, mqtt=send_mqtt)
                    if send_mqtt:
                        last_full_frame = time.time()

                    average_temp = compute_average_temp(mlx_data_frame)
                    data_logger.log_data(name="tire_temp_avg", value=average_temp)
                except Exception as e:
                    log(f"Error reading MLX90640 frame: {e}")

            if adc_active:
                try:
                    adc = sensors.get("adc")
                    adc_data = read_adc(adc)
                    data_logger.log_data(name="linpot", value=adc_data)
                except Exception as e:
                    log(f"Error reading ADC: {e}")

            if vl53l0x_active:
                try:
                    vl53 = sensors.get("vl53")
                    ride_height = read_range(vl53)
                    data_logger.log_data(name="ride_height", value=ride_height)
                except Exception as e:
                    log(f"Error reading VL53L0X: {e}")

        else:
            if mlx_active:
                try :
                    tire_temp_frame = []
                    for i in range(24 * 32):
                        tire_temp_frame.append(random.randint(1000, 9999))
                    send_mqtt =not last_full_frame or  (time.time() - last_full_frame) > 1
                    data_logger.log_data(name="tire_temp_frame", value=tire_temp_frame, mqtt=send_mqtt)
                    average_temp = compute_average_temp(tire_temp_frame)
                    data_logger.log_data(name="tire_temp_avg", value=average_temp)
                except Exception as e:
                    log(f"Error reading MLX90640 frame: {e}")

            if adc_active:
                try:
                    adc_data = random.randint(1, 100)
                    data_logger.log_data(name="linpot", value=adc_data)
                except Exception as e:
                    log(f"Error reading ADC: {e}")

            if vl53l0x_active:
                try:
                    ride_height = random.randint(1,50)
                    data_logger.log_data(name="ride_height", value=ride_height)
                except Exception as e:
                    log(f"Error reading VL53L0X: {e}")
            # Generate random data in dry-run mode

            time.sleep(0.4)

        # log(f"Collected sensor data: {msg}")
        if not mlx_active:
            time.sleep(0.1)  # Adjust as needed for data rate

        # except Exception as e:
        # log(f"Error reading sensors: {e}")


def main():
    if not is_test_mode:
        # Initialize I2C buses and sensors once
        i2c1 = busio.I2C(board.SCL, board.SDA)
        i2c0 = busio.I2C(board.D1, board.D0)

        if adc_active:
            sensors["adc"] = init_max11617(i2c0)
        if vl53l0x_active:
            sensors["vl53"] = init_vl53l0x(i2c0)
        if mlx_active:
            sensors["mlx"] = init_mlx90640()

    # Start the MQTT thread
    mqtt_thread_instance = threading.Thread(target=mqtt.run_connection, args=(args.ip_address, handle_message), daemon=True)
    mqtt_thread_instance.start()

    # Start the sensor reading thread
    sensor_thread_instance = threading.Thread(target=read_sensors, daemon=True)
    sensor_thread_instance.start()

    # Keep the main thread alive to allow other threads to run
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        log("Shutting down due to KeyboardInterrupt...")
        mqtt.disconnect()


if __name__ == "__main__":
    main()
