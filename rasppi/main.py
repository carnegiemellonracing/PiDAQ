import os
import time
import paho.mqtt.client as mqtt
import random
import argparse
import json
import datetime
import threading
import queue

# Constants
BROKER_ADDRESS = "test.mosquitto.org"
BROKER_PORT = 1883

# toggle sensors
DISCONNECT_TIMEOUT_SECONDS = 300
CSV_HEADER = "timestamp,tire_temp_frame,linpot,ride_height\n"

def make_csv_line(data):
    return f"{str(time.time())},\"{data['tire_temp_frame']}\",{data['linpot']},{data['ride_height']}\n"


def get_file_name(test_name, timestamp):
    return os.path.join(
        "tests/",
        f"{timestamp.strftime('%Y_%m_%d/%H_%M')} {test_name}_PI{DAQ_PI_ID}.csv",
    )


def open_file_with_directories(file_path, mode="w"):
    # Extract the directory from the file path
    directory = os.path.dirname(file_path)

    # Check if the directory exists, and if not, create it
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    # Now open the file
    return open(file_path, mode)


def log(msg):
    print(f"[{datetime.datetime.now()}] {msg}")


# Thread-safe queue for MQTT messages
mqtt_queue = queue.Queue()

# Lock to control shared state access
lock = threading.Lock()

# Get Pi ID from environment or set randomly in test mode
DAQ_PI_ID = os.getenv("DAQ_PI_ID") or f"RPI-{random.randint(1000, 9999)}"

# MQTT topics
COMMAND_TOPIC = "commands"
DATA_TOPIC = "data"
STATUS_TOPIC = "status"

# Command-line argument parsing
parser = argparse.ArgumentParser(description="Process CLI arguments.")
parser.add_argument("-t", "--test_mode", action="store_true", help="Run in test mode")
parser.add_argument("-a", "--adc", action="store_true", help="Enable ADC sensor")
parser.add_argument("-m", "--mlx", action="store_true", help="Enable MLX90640 sensor")
parser.add_argument("-v", "--vl", action="store_true", help="Enable VL53L0X sensor")

args = parser.parse_args()
is_test_mode = args.test_mode
adc_active = args.adc
mlx_active = args.mlx
vl53l0x_active = args.vl

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


# Initialize MQTT client: custom client ID, LWT
client = mqtt.Client()
lwt_payload = {"id": DAQ_PI_ID, "status": "offline"}
client.will_set(STATUS_TOPIC, payload=json.dumps(lwt_payload), qos=1, retain=True)


class TestingState:
    def __init__(self):
        self.test_state = False
        self.test_time_stamp = None
        self.test_name = ""
        self.dry_run = bool(is_test_mode)
        self.daq_pi_id = DAQ_PI_ID if DAQ_PI_ID is not None else random.randint(1, 100)

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


# MQTT event listeners
def on_connect(client, userdata, flags, rc):
    log(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(COMMAND_TOPIC, qos=1)
    payload = {"id": DAQ_PI_ID, "status": "online"}
    client.publish(STATUS_TOPIC, json.dumps(payload), qos=1)


def on_message(client, userdata, msg):
    log(f"Received message from topic '{msg.topic}': {msg.payload.decode()}")

    if msg.topic == COMMAND_TOPIC:
        data = json.loads(msg.payload.decode())
        test_name = data["test_name"]
        if data["command"] == "start":
            testStateManager.start_test(test_name, datetime.datetime.now())
            log(f'Started test: "{test_name}"')
        elif data["command"] == "stop":
            testStateManager.stop_test()
            log(f'Stopped test: "{test_name}"')


client.on_connect = on_connect
client.on_message = on_message


# Thread to handle MQTT communication and publish messages from the queue.
def mqtt_thread():
    client.connect(BROKER_ADDRESS, BROKER_PORT, keepalive=5)
    client.loop_start()  # Start MQTT loop in the background

    while True:
        try:
            # Get the next message from the queue
            msg = mqtt_queue.get()  # This will block until a message is available
            topic, payload = msg
            client.publish(topic, payload, qos=0)
            # log(f"Published to {topic}: {payload}")
            mqtt_queue.task_done()  # Mark the task as done
        except Exception as e:
            log(f"Error in MQTT thread: {e}")


# Thread to collect sensor data and place it in the MQTT queue.
def read_sensors():
    while True:
        with lock:
            if not testStateManager.test_state:
                time.sleep(1)  # Avoid busy waiting
                continue

        try:
            # Prepare sensor data
            if (testStateManager.test_state):
                data = {
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "tire_temp_frame": random.randint(20, 40) if mlx_active else None,
                    "linpot": random.randint(1, 100) if adc_active else None,
                    "ride_height": random.randint(1, 50) if vl53l0x_active else None,
                }

                msg = {
                    "id": DAQ_PI_ID,
                    "testName": testStateManager.test_name,
                    "test_data": data,
                }

                # Place the message into the MQTT queue
                mqtt_queue.put((DATA_TOPIC, json.dumps(msg)))

                # log(f"Collected sensor data: {msg}")
                time.sleep(0.2)  # Adjust as needed for data rate

        except Exception as e:
            log(f"Error reading sensors: {e}")


def main():
    # Start the MQTT thread
    mqtt_thread_instance = threading.Thread(target=mqtt_thread, daemon=True)
    mqtt_thread_instance.start()

    # Start the sensor reading thread
    sensor_thread_instance = threading.Thread(target=read_sensors, daemon=True)
    sensor_thread_instance.start()

    # Keep the main thread alive to allow other threads to run
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        log("Shutting down...")
        client.disconnect()


if __name__ == "__main__":
    main()
