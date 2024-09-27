import os
import time
import socketio
import random
import argparse

# sensors
from sensors.max11617 import read_adc
from sensors.vl53l0x import read_range
from sensors.mlx90640 import read_frame

sio = socketio.Client()

# get Pi ID from env var
DAQ_PI_ID = os.getenv("DAQ_PI_ID")

# set up and parse command line arguments
parser = argparse.ArgumentParser(description="Process CLI arguments.")

parser.add_argument("ip_address", type=str, help="IP address of the WebSocket Server")
parser.add_argument(
    "-t", "--test_mode", type=bool, help="An optional argument", default=False
)

args = parser.parse_args()
wss_ip = args.first_arg
is_test_mode = args.test_mode
print(f"WS server address: {wss_ip}")
if is_test_mode:
    print("Running in dry run test mode.")
else:
    print("Running in normal mode.")


# Raspberry Pi test collection state machine
class TestingState:
    def __init__(self):
        self.test_state = False
        self.test_name = ""
        self.dry_run = is_test_mode is None
        if DAQ_PI_ID is None:
            print(
                "WARNING: Raspberry Pi ID could not be read from system. Setting a random ID for testing purposes."
            )
            DAQ_PI_ID = random.randint(1, 100)

    def get_name(self):
        return self.test_name

    def set_name(self, test_name):
        self.test_name = test_name

    def get_state(self):
        return self.test_state

    def set_state(self, test_state):
        self.test_state = test_state


# testing vars
testStateManager = TestingState()


@sio.event
def connect():
    sio.emit("join_rpi", {"env": f"rpi{DAQ_PI_ID}"})
    print("connection established")


@sio.event
def connect_error(data):
    print("The connection failed")


@sio.event
def disconnect():
    print("Disconnected from server")


@sio.on("start_test")
def start_test(test_name):
    print(f'starting test "{test_name}"')
    testStateManager.set_state(True)
    testStateManager.set_name(test_name)


@sio.on("stop_test_rpi")
def stop_test(test_name):
    print(f'stopped test "{test_name}"')
    testStateManager.set_state(False)
    testStateManager.set_name("")


def main():
    # connect to ws server
    sio.connect(wss_ip)

    while testStateManager.get_test_state():
        # collect sensor data
        linpot_value = read_adc()
        ride_height_value = read_range()
        tire_temp_frame = read_frame()

        # testing mode
        if is_test_mode:
            dv = random.randint(1, 100)
            idv = int(time.time())
            sio.emit(
                "test_data",
                {
                    "testName": testStateManager.get_name(),
                    "data": [idv, dv],
                },
            )
        else:
            sio.emit(
                "test_data",
                {
                    "testName": testStateManager.get_name(),
                    "data": {
                        "tire_temp_frame": tire_temp_frame,
                        "linpot": linpot_value,
                        "ride_height": ride_height_value,
                    },
                },
            )

    sio.wait()


if __name__ == "__main__":
    main()
