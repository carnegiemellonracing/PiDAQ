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
BROKER_ADDRESS = "localhost"
BROKER_PORT = 1883
CSV_HEADER = "timestamp,tire_temp_frame,linpot,ride_height\n"

# Thread-safe queue for MQTT messages
mqtt_queue = queue.Queue()

# Lock to control shared state access
lock = threading.Lock()

# Get Pi ID from environment or set randomly in test mode
DAQ_PI_ID = os.getenv("DAQ_PI_ID") or f"RPI-{random.randint(1, 100)}"

# MQTT topics
COMMAND_TOPIC = "command_stream"
DATA_TOPIC = "data_stream"
STATUS_TOPIC = "status"

# Command-line argument parsing
parser = argparse.ArgumentParser(description="Process CLI arguments.")
parser.add_argument("ip_address", type=str, help="IP address of the WebSocket Server")
parser.add_argument("-t", "--test_mode", action="store_true", help="Run in test mode")
parser.add_argument("-a", "--adc", action="store_true", help="Enable ADC sensor")
parser.add_argument("-m", "--mlx", action="store_true", help="Enable MLX90640 sensor")
parser.add_argument("-v", "--vl", action="store_true", help="Enable VL53L0X sensor")

args = parser.parse_args()
is_test_mode = args.test_mode
adc_active = args.adc
mlx_active = args.mlx
vl53l0x_active = args.vl

# Initialize MQTT client: custom client ID, LWT
client_id = f"RPI-{DAQ_PI_ID}"
client = mqtt.Client(client_id)
lwt_payload = {"id": client_id, "status": "offline"}
client.will_set(STATUS_TOPIC, payload=json.dumps(lwt_payload), qos=1, retain=True)


class TestingState:
    def __init__(self):
        self.test_state = False
        self.test_name = ""
        self.test_timestamp = None
        self.dry_run = is_test_mode

    def start_test(self, name, timestamp):
        self.test_name = name
        self.test_timestamp = timestamp
        self.test_state = True

    def stop_test(self):
        self.test_state = False
        self.test_name = ""
        self.test_timestamp = None


testStateManager = TestingState()


def log(msg):
    print(f"[{datetime.datetime.now()}] {msg}")


# MQTT event listeners
def on_connect(client, userdata, flags, rc):
    log(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(COMMAND_TOPIC, qos=1)
    payload = {"id": client_id, "status": "online"}
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
    client.connect(BROKER_ADDRESS, BROKER_PORT, keepalive=60)
    client.loop_start()  # Start MQTT loop in the background

    while True:
        try:
            # Get the next message from the queue
            msg = mqtt_queue.get()  # This will block until a message is available
            topic, payload = msg
            client.publish(topic, payload, qos=0)
            log(f"Published to {topic}: {payload}")
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
            data = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "tire_temp_frame": random.randint(20, 40) if mlx_active else None,
                "linpot": random.randint(1, 100) if adc_active else None,
                "ride_height": random.randint(1, 50) if vl53l0x_active else None,
            }

            msg = {
                "testName": testStateManager.test_name,
                "data": data,
            }

            # Place the message into the MQTT queue
            mqtt_queue.put((DATA_TOPIC, json.dumps(msg)))

            log(f"Collected sensor data: {msg}")
            time.sleep(1)  # Adjust as needed for data rate

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
            time.sleep(1)
    except KeyboardInterrupt:
        log("Shutting down...")
        client.disconnect()


if __name__ == "__main__":
    main()
