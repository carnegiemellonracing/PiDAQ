import os
import time
import socketio
import random
import argparse
import datetime
import numpy as np

sio = socketio.Client()

# get Pi ID from env var
DAQ_PI_ID = os.getenv("DAQ_PI_ID")

# toggle sensors
# set up and parse command line arguments
parser = argparse.ArgumentParser(description="Process CLI arguments.")

parser.add_argument("ip_address", type=str, help="IP address of the WebSocket Server")

args = parser.parse_args()
wss_ip = args.ip_address

if DAQ_PI_ID is None:
    DAQ_PI_ID = random.randint(1, 100)

print(f"WS server address: {wss_ip}")

# Raspberry Pi test collection state machine
class TestingState:
    def __init__(self):
        self.test_state = False
        self.test_time_stamp = None
        self.test_name = ""
        self.dry_run = True
        self.daq_pi_id = DAQ_PI_ID if DAQ_PI_ID is not None else random.randint(1, 100)

        if self.daq_pi_id is None:
            print(
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
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    testStateManager.start_test(test_name=test_name, timestamp=timestamp)


@sio.on("stop_test_rpi")
def stop_test(test_name):
    print(f'stopped test "{test_name}"')
    testStateManager.set_state(False)
    testStateManager.set_name("")


def main():
    # connect to ws server
    try:
        sio.connect(wss_ip)
    except socketio.exceptions.ConnectionError:
        print(f"Failed to connect to {wss_ip}")
        return

    # init sensors
    last_test_name = None
    while True:
        if testStateManager.get_state():
            print("got into the while loop")
            # collect sensor data

            # testing mode
            try:
                formatted_data = {
                    "tire_temp_frame":
                        list(30 + (70 - 30) * np.random.rand(768)),
                    "linpot": random.randint(1, 10),
                    "ride_height": random.randint(6, 16),
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
                sio.emit(
                    "test_data",
                    {
                        "testName": testStateManager.get_name(),
                        "data": formatted_data,
                    },
                )
            except Exception as e:
                print(e)
                print(sio)
            time.sleep(0.1)

if __name__ == "__main__":
    main()
