import os
import time
import socketio
import random
import argparse
import board
import busio
import datetime

# sensors
from sensors.max11617 import init_max11617, read_adc
from sensors.vl53l0x import init_vl53l0x, read_range
from sensors.mlx90640 import init_mlx90640, read_frame

sio = socketio.Client()

# get Pi ID from env var
DAQ_PI_ID = os.getenv("DAQ_PI_ID")

# toggle sensors
ADC_ACTIVE = False
MLX_90640_ACTIVE = True
VL53L0X_ACTIVE = False

CSV_HEADER = "timestamp,tire_temp_frame,linpot,ride_height\n"


def make_csv_line(data):
    return f"{str(time.time())},\"{data['tire_temp_frame']}\",{data['linpot']},{data['ride_height']}\n"


def get_file_name(test_name, timestamp):
    return os.path.join(
        "tests/", f"{timestamp.strftime('%Y_%m_%d/%H_%M')} {test_name}.csv"
    )

def open_file_with_directories(file_path, mode='w'):
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


args = parser.parse_args()
wss_ip = args.ip_address
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
        self.test_time_stamp = None
        self.test_name = ""
        self.dry_run = bool(is_test_mode)
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
    i2c1 = busio.I2C(board.SCL, board.SDA)
    i2c0 = busio.I2C(board.D1, board.D0)

    if ADC_ACTIVE:
        adc = init_max11617(i2c0)

    if VL53L0X_ACTIVE:
        tof = init_vl53l0x(i2c0)

    if MLX_90640_ACTIVE:
        tt = init_mlx90640(i2c1)

    last_test_name = None

    while True:
        if testStateManager.get_state():
            with open_file_with_directories(
                get_file_name(
                    testStateManager.get_name(), testStateManager.get_timestamp()
                ),
                "a",
            ) as file:
                if last_test_name != testStateManager.get_name():
                    last_test_name = testStateManager.get_name()
                    file.write(CSV_HEADER)
                while True:
                    print("got into the while loop")
                    # collect sensor data
                    if ADC_ACTIVE:
                        linpot_value = read_adc(adc)
                    if VL53L0X_ACTIVE:
                        ride_height_value = read_range(tof)
                    if MLX_90640_ACTIVE:
                        tire_temp_frame = read_frame(tt)

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
                        formatted_data = {
                            "tire_temp_frame": (
                                tire_temp_frame if MLX_90640_ACTIVE else False
                            ),
                            "linpot": linpot_value if ADC_ACTIVE else False,
                            "ride_height": (ride_height_value if VL53L0X_ACTIVE else False),
                        }
                        # sio.emit(
                        #     "test_data",
                        #     {
                        #         "testName": testStateManager.get_name(),
                        #         "data": formatted_data,
                        #     },
                        # )
                        file.write(make_csv_line(formatted_data))


if __name__ == "__main__":
    main()
