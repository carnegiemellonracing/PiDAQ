# Updated imports - removed deprecated sensors and CAN bus
from max11617.max11617 import MAX11617  # Using MAX11617 driver for AD7991 ADC
from mlx90640.mlx90640 import MLX90640
from mlx90640_1.mlx90640_1 import MLX90640_1

from multiprocessing import Process, Queue, Value, Array
from smbus2 import SMBus
from threading import Thread, Lock
from datetime import datetime

import os
import busio
import board
import serial
import RPi.GPIO as GPIO
import time

import csv
import subprocess

from pathlib import Path
from cedargrove_nau7802 import NAU7802

# TODO: change way of doing this
if "DAQ_PI_ID" in os.environ:
    DAQ_PI_ID = int(os.getenv("DAQ_PI_ID"))
else:
    DAQ_PI_ID = 4

# Task timing constants
MLX90640_TASK_PERIOD = 0.125
AD7991_TASK_PERIOD = 0.005
NAU7802_TASK_PERIOD = 0.1  # 10 Hz read rate for linpots

# MLX90640 IR thermal camera
MLX90640_ADDRESS = 0x33
MLX90640_FRAME_RATE = 8.0

# NAU7802 load cell / linpot ADC
NAU7802_ADDRESS = 0x2A

TIME_1MS = 0.001

LOG_DIRECTORY = str(Path(__file__).parent.absolute()) + "/../log/"
LAST_GOOD_TIME_FILE = "last_good_time.txt"


# --- NAU7802 helper functions (from linpot test script) ---

def init_nau7802(i2c, name):
    """Initialize a NAU7802 ADC on the given I2C bus.
    
    Args:
        i2c: I2C bus handle (busio.I2C)
        name: Label for logging (e.g. "I2C0", "I2C1")
    
    Returns:
        NAU7802 instance or None if init failed
    """
    try:
        adc = NAU7802(i2c, address=NAU7802_ADDRESS, active_channels=1)
        adc.enable(True)
        time.sleep(0.1)  # IMPORTANT: allow power-up

        adc.channel = 1
        adc.gain = 1

        print(f"{name} NAU7802: OK")
        return adc
    except Exception as e:
        print(f"{name} NAU7802: FAILED -> {e}")
        return None


def read_linpot_mm(adc, lock=None):
    """Read linear potentiometer value from NAU7802 in mm.
    
    Args:
        adc: NAU7802 instance (or None)
        lock: threading.Lock to synchronize I2C bus access (optional)
    
    Returns:
        Linear potentiometer travel in mm, or None if ADC unavailable
    """
    if adc is None:
        return None

    if lock:
        lock.acquire()
    try:
        while not adc.available():
            pass
        voltage_uv = (adc.read() / 16777215) * 3300000
    finally:
        if lock:
            lock.release()

    linpot_travel_um = (voltage_uv - 7230) / -96.1
    return linpot_travel_um / 1000


def i2c0_process(smbus_handle, busio_handle, avg_temp_value, ir_frame_update, ir_frame_array, linpot_reading):
    # TODO: RTC code

    mlx_enabled = False
    nau_enabled = False
    bus_lock = Lock()  # Protect shared I2C0 bus between MLX (SMBus) and NAU (busio)

    try:
        mlx = MLX90640(smbus_handle, i2c_addr=MLX90640_ADDRESS, frame_rate=MLX90640_FRAME_RATE)
        mlx_enabled = True
    except Exception as e:
        print("MLX0 not detected")

    adc = init_nau7802(busio_handle, "I2C0")
    if adc is not None:
        nau_enabled = True

    def mlx90640_task():
        while True:
            bus_lock.acquire()
            try:
                avg_temp, frame = mlx.read_frame()
            finally:
                bus_lock.release()

            if avg_temp is not None:
                avg_temp_value.value = avg_temp

                # TODO: toggle with XOR
                if ir_frame_update.value == 0:
                    ir_frame_update.value = 1
                else:
                    ir_frame_update.value = 0

                for i, value in enumerate(frame):
                    ir_frame_array[i] = value


    def nau_task():
        """Continuously read linpot via NAU7802 at NAU7802_TASK_PERIOD rate."""
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > NAU7802_TASK_PERIOD:
                value_mm = read_linpot_mm(adc, bus_lock)
                if value_mm is not None:
                    linpot_reading.value = int(value_mm * 1000)  # Store as um in shared int
                start_time = current_time
            else:
                time.sleep(TIME_1MS)

    mlx90640_thread = Thread(target=mlx90640_task)
    nau_thread = Thread(target=nau_task)

    if mlx_enabled:
        mlx90640_thread.start()
    if nau_enabled:
        nau_thread.start()

    # Keep process alive if at least one thread is running
    while True:
        time.sleep(1)


def i2c1_process(smbus_handle, busio_handle, avg_temp_value, ir_frame_update, ir_frame_array, linpot_reading):

    mlx_enabled = False
    nau_enabled = False
    bus_lock = Lock()  # Protect shared I2C1 bus

    try:
        mlx = MLX90640_1(smbus_handle, i2c_addr=MLX90640_ADDRESS, frame_rate=MLX90640_FRAME_RATE)
        mlx_enabled = True
    except Exception as e:
        print("MLX1 not detected")


    adc = init_nau7802(busio_handle, "I2C1")
    if adc is not None:
        nau_enabled = True

    # TODO: take this func outta this func so that the two processes can share code
    def mlx90640_task():
        while True:
            bus_lock.acquire()
            try:
                avg_temp, frame = mlx.read_frame()
            finally:
                bus_lock.release()

            if avg_temp is not None:
                avg_temp_value.value = avg_temp

                if ir_frame_update.value == 0:
                    ir_frame_update.value = 1
                else:
                    ir_frame_update.value = 0

                for i, value in enumerate(frame):
                    ir_frame_array[i] = value


    def nau_task():
        """Continuously read linpot via NAU7802 at NAU7802_TASK_PERIOD rate."""
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > NAU7802_TASK_PERIOD:
                value_mm = read_linpot_mm(adc, bus_lock)
                if value_mm is not None:
                    linpot_reading.value = int(value_mm * 1000)  # Store as um in shared int
                start_time = current_time
            else:
                time.sleep(TIME_1MS)

    mlx90640_thread = Thread(target=mlx90640_task)
    nau_thread = Thread(target=nau_task)

    if mlx_enabled:
        mlx90640_thread.start()
    if nau_enabled:
        nau_thread.start()

    # Keep process alive
    while True:
        time.sleep(1)


def log_process(avg_temp0_value, ir_frame0_update, ir_frame0_array,
                avg_temp1_value, ir_frame1_update, ir_frame1_array,
                i2c0_linpot_reading, i2c1_linpot_reading):

    # -----------------------
    # Time utilities
    # -----------------------
    def is_time_synced():
        try:
            output = subprocess.check_output(["timedatectl"], text=True)
            return "System clock synchronized: yes" in output
        except:
            return False

    def get_timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    def get_safe_start_time():
        if is_time_synced():
            now = datetime.now()
            with open(LAST_GOOD_TIME_FILE, "w") as f:
                f.write(now.isoformat())
            return now, True

        if os.path.exists(LAST_GOOD_TIME_FILE):
            with open(LAST_GOOD_TIME_FILE, "r") as f:
                last = f.read().strip()
                return datetime.fromisoformat(last), False

        return datetime.now(), False


    # -----------------------
    # Setup
    # -----------------------
    os.makedirs(LOG_DIRECTORY, exist_ok=True)

    file_handle = None
    writer = None
    last_update_value = 0

    start_time, rtc_ok = get_safe_start_time()
    timestamp_label = start_time.strftime("%Y-%m-%d_%H-%M-%S")

    filename = (
        f"{LOG_DIRECTORY}/{timestamp_label}.csv"
        if rtc_ok
        else f"{LOG_DIRECTORY}/NO_RTC_last_{timestamp_label}.csv"
    )

    file_handle = open(filename, "w", newline="")
    writer = csv.writer(file_handle)

    # header
    writer.writerow([
        "timestamp",
        "ir_frame0",
        "ir_frame1",
        "avg_temp0",
        "avg_temp1",
        "FL_linpot",
        "FR_linpot"
    ])
    file_handle.flush()

    # -----------------------
    # Main loop
    # -----------------------
    while True:

        if ir_frame0_update.value != last_update_value:

            writer.writerow([
                get_timestamp(),
                list(ir_frame0_array),
                list(ir_frame1_array),
                avg_temp0_value.value,
                avg_temp1_value.value,
                -i2c1_linpot_reading.value/1000,
                -i2c0_linpot_reading.value/1000
            ])

            file_handle.flush()
            last_update_value = ir_frame0_update.value

        time.sleep(0.001)
    
    


if __name__ == "__main__":
    # --- Init I2C buses ---
    # Each bus needs TWO handles:
    #   SMBus  -> for MLX90640 and AD7991 drivers
    #   busio  -> for NAU7802 CircuitPython driver

    # I2C1 (default Pi I2C: SCL/SDA on GPIO 2/3)
    i2c1_smbus = SMBus(1)
    i2c1_busio = busio.I2C(board.SCL, board.SDA)

    # I2C0 (secondary bus: GPIO 1/0)
    try:
        i2c0_smbus = SMBus(0)
        i2c0_busio = busio.I2C(board.D1, board.D0)
        i2c0_available = True
    except Exception as e:
        print(f"I2C0 init failed: {e}")
        i2c0_available = False

    # Shared values for inter-process communication
    avg_temp0_value = Value("i", 0)
    avg_temp1_value = Value("i", 0)
    ir_frame0_array = Array("i", 32 * 24)
    ir_frame1_array = Array("i", 32 * 24)
    ir_frame0_update = Value("b", 0)
    ir_frame1_update = Value("b", 0)

    # Linpot readings (stored as integer micrometers for shared Value)
    i2c0_linpot_reading = Value("i", 0)
    i2c1_linpot_reading = Value("i", 0)

    # Test ID control (TODO: implement control mechanism - button/GPIO/network)
    test_id_value = Value("i", 0)

    # Create processes
    i2c0_proc = Process(
        target=i2c0_process,
        args=(i2c0_smbus, i2c0_busio, avg_temp0_value, ir_frame0_update, ir_frame0_array, i2c0_linpot_reading)
    ) if i2c0_available else None

    i2c1_proc = Process(
        target=i2c1_process,
        args=(i2c1_smbus, i2c1_busio, avg_temp1_value, ir_frame1_update, ir_frame1_array, i2c1_linpot_reading)
    )

    log_process = Process(target=log_process, args=(avg_temp0_value, ir_frame0_update, ir_frame0_array, avg_temp1_value, 
                ir_frame1_update, ir_frame1_array, i2c0_linpot_reading, i2c1_linpot_reading,))

    # Start all processes
    print("Starting CMR Data Acquisition System...")
    print(f"DAQ Pi ID: {DAQ_PI_ID}")

    if i2c0_proc is not None:
        i2c0_proc.start()
    else:
        print("I2C0 process skipped (bus not available)")

    i2c1_proc.start()
    log_process.start()

    while True:
        i2c0_mm = -i2c0_linpot_reading.value / 1000.0
        i2c1_mm = -i2c1_linpot_reading.value / 1000.0
        print(f"MAIN LOOP: Temp0: {avg_temp0_value.value}, Temp1: {avg_temp1_value.value}, Linpot I2C0: {i2c0_mm:.2f} mm, Linpot I2C1: {i2c1_mm:.2f} mm")
