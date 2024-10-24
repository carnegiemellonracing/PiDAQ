import os
import time
import paho.mqtt.client as mqtt
import time
import random
import argparse
import json
import datetime
import threading

# sensors
# from sensors.max11617 import init_max11617, read_adc
# from sensors.vl53l0x import init_vl53l0x, read_range
# from sensors.mlx90640 import init_mlx90640, read_frame

# Lock for controlling concurrent access to try_connect
lock = threading.Lock()


def log(msg):
    print(f"[{time.time()}] {msg}")


# get Pi ID from env var
DAQ_PI_ID = os.getenv("DAQ_PI_ID")

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


# set up and parse command line arguments
parser = argparse.ArgumentParser(description="Process CLI arguments.")

parser.add_argument("ip_address", type=str, help="IP address of the WebSocket Server")
parser.add_argument("-t", "--test_mode", action="store_true", help="Run in test mode")
parser.add_argument("-a", "--adc", action="store_true", help="Enable ADC sensor")
parser.add_argument("-m", "--mlx", action="store_true", help="Enable MLX90640 sensor")
parser.add_argument("-v", "--vl", action="store_true", help="Enable VL53L0X sensor")

args = parser.parse_args()
wss_ip = args.ip_address
is_test_mode = args.test_mode
adc_active = args.adc
mlx_active = args.mlx
vl53l0x_active = args.vl

if DAQ_PI_ID is None:
    if is_test_mode:
        log("WARNING: DAQ_PI_ID not set in environment. Using random value")
        DAQ_PI_ID = random.randint(1, 100)
    else:
        log("ERROR: DAQ_PI_ID not set in environment.")
        exit(1)

if is_test_mode:
    log("Running in dry run test mode.")
else:
    log("Running in normal mode.")
    import board
    import busio
    from sensors.max11617 import init_max11617, read_adc
    from sensors.vl53l0x import init_vl53l0x, read_range
    from sensors.mlx90640 import init_mlx90640, read_frame


# Raspberry Pi test collection state machine
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


# testing vars
testStateManager = TestingState()


# MQTT topics
commandTopic = "command_stream"
dataTopic = "data_stream"
BROKER_ADDRESS = "localhost"  # Local broker address
BROKER_PORT = 1883  # Default MQTT port

client_id = f"RPI-{DAQ_PI_ID})"
client = mqtt.Client(client_id)


def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

    # Subscribe to a topic with QoS 1
    client.subscribe("command_stream", qos=1)


def on_message(client, userdata, msg):
    print(f"Received message from topic '{msg.topic}': {msg.payload.decode()}")
    if msg.topic != commandTopic:
        return
    data = json.loads(msg.payload.decode())
    command = data["command"]

    if command == "start":
        test_name = data["test_name"]
        log(f'starting test "{test_name}"')
        timestamp = datetime.datetime.now(datetime.timezone.utc)
        testStateManager.start_test(test_name=test_name, timestamp=timestamp)

    if command == "stop":
        test_name = data["test_name"]
        log(f'stopped test "{test_name}"')
        testStateManager.set_state(False)
        testStateManager.set_name("")


# Assign event handlers
client.on_connect = on_connect
client.on_message = on_message


def read_sensors():
    while True:

        with lock:
            if not testStateManager.get_state():
                print("Data collection stopped.")
                continue

        try:

            file_name = (
                get_file_name(
                    testStateManager.get_name(), testStateManager.get_timestamp()
                ),
            )

            with open_file_with_directories(
                file_name,
                "a",
            ) as file:
                if last_test_name != testStateManager.get_name():
                    last_test_name = testStateManager.get_name()
                    file.write(CSV_HEADER)

                # collect sensor data
                if adc_active:
                    linpot_value = read_adc(adc)
                if vl53l0x_active:
                    ride_height_value = read_range(tof)
                if mlx_active:
                    tire_temp_frame = read_frame(tt)

                # dry-run mode: sends random data back to server
                if testStateManager.dry_run:
                    dv = random.randint(1, 100)
                    idv = int(time.time())

                    msg = {
                        "testName": testStateManager.get_name(),
                        "data": [idv, dv],
                    }

                    client.publish(dataTopic, json.loads(msg), {qos: 0})

                # real shit dawg
                else:
                    formatted_data = {
                        "tire_temp_frame": (tire_temp_frame if mlx_active else False),
                        "linpot": linpot_value if adc_active else False,
                        "ride_height": (ride_height_value if vl53l0x_active else False),
                        "timestamp": datetime.datetime.now(
                            datetime.timezone.utc
                        ).isoformat(),
                    }

                    msg = {
                        "testName": testStateManager.get_name(),
                        "data": formatted_data,
                    }

                    client.publish(dataTopic, json.loads(msg), {qos: 0})

                    file.write(make_csv_line(formatted_data))

        except Exception as e:
            print(f"Error reading frame: {e}")


def main():

    # Connect to the broker with the custom client ID
    client.connect(BROKER_ADDRESS, BROKER_PORT, keepalive=60)

    # Start a non-blocking network loop
    client.loop_start()

    # init sensors
    if not testStateManager.dry_run:
        i2c1 = busio.I2C(board.SCL, board.SDA)
        i2c0 = busio.I2C(board.D1, board.D0)

        if adc_active:
            adc = init_max11617(i2c0)

        if vl53l0x_active:
            tof = init_vl53l0x(i2c0)

        if mlx_active:
            tt = init_mlx90640()

        # open file, write data


if __name__ == "__main__":
    main()
