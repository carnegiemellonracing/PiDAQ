# Updated imports - removed deprecated sensors and CAN bus
from max11617.max11617 import MAX11617  # Using MAX11617 driver for AD7991 ADC
from mlx90640.mlx90640 import MLX90640
from mlx90640_1.mlx90640_1 import MLX90640_1

from multiprocessing import Process, Queue, Value, Array
from smbus2 import SMBus
from threading import Thread
from datetime import datetime

import os
import busio
import board
import serial
import RPi.GPIO as GPIO
import time

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

# AD7991 ADC (4-channel 12-bit ADC)
AD7991_ADDRESS = 0x28  # AD7991-0 address, if -0 then 0x29
AD7991_CHANNEL_COUNT = 4

# NAU7802 load cell / linpot ADC
NAU7802_ADDRESS = 0x2A

TIME_1MS = 0.001

LOG_DIRECTORY = str(Path(__file__).parent.absolute()) + "/../log/"


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


def read_linpot_mm(adc):
    """Read linear potentiometer value from NAU7802 in mm.
    
    Args:
        adc: NAU7802 instance (or None)
    
    Returns:
        Linear potentiometer travel in mm, or None if ADC unavailable
    """
    if adc is None:
        return None

    while not adc.available():
        pass

    voltage_uv = (adc.read() / 16777215) * 3300000
    linpot_travel_um = (voltage_uv - 7230) / -96.1
    return linpot_travel_um / 1000


def i2c0_process(i2c_handle, avg_temp_value, ir_frame_update, ir_frame_array, linpot_reading):
    # TODO: RTC code

    mlx_enabled = False
    nau_enabled = False

    try:
        mlx = MLX90640(i2c_handle, i2c_addr=MLX90640_ADDRESS, frame_rate=MLX90640_FRAME_RATE)
        mlx_enabled = True
    except Exception as e:
        print("MLX0 not detected")

    adc = init_nau7802(i2c_handle, "I2C0")
    if adc is not None:
        nau_enabled = True

    def mlx90640_task():
        while True:
            avg_temp, frame = mlx.read_frame()

            if avg_temp is not None:
                avg_temp_value.value = avg_temp

                # TODO: toggle with XOR
                if ir_frame_update.value == 0:
                    ir_frame_update.value = 1
                else:
                    ir_frame_update.value = 0

                for i, value in enumerate(frame):
                    ir_frame_array[i] = value

                print("i2c0 temp:", avg_temp)

    def nau_task():
        """Continuously read linpot via NAU7802 at NAU7802_TASK_PERIOD rate."""
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > NAU7802_TASK_PERIOD:
                value_mm = read_linpot_mm(adc)
                if value_mm is not None:
                    linpot_reading.value = int(value_mm * 1000)  # Store as um in shared int
                    print(f"I2C0 linpot: {value_mm:.2f} mm")
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


def i2c1_process(i2c_handle, avg_temp_value, ir_frame_update, ir_frame_array, linpot_reading):

    mlx_enabled = False
    ad7991_enabled = False
    nau_enabled = False

    try:
        mlx = MLX90640_1(i2c_handle, i2c_addr=MLX90640_ADDRESS, frame_rate=MLX90640_FRAME_RATE)
        mlx_enabled = True
    except Exception as e:
        print("MLX1 not detected")

    try:
        ad7991 = MAX11617(i2c_handle, AD7991_ADDRESS, AD7991_CHANNEL_COUNT)
        ad7991_enabled = True
    except Exception as e:
        print(f"AD7991 (ADC) not detected")

    adc = init_nau7802(i2c_handle, "I2C1")
    if adc is not None:
        nau_enabled = True

    # TODO: take this func outta this func so that the two processes can share code
    def mlx90640_task():
        while True:
            avg_temp, frame = mlx.read_frame()

            if avg_temp is not None:
                avg_temp_value.value = avg_temp

                if ir_frame_update.value == 0:
                    ir_frame_update.value = 1
                else:
                    ir_frame_update.value = 0

                for i, value in enumerate(frame):
                    ir_frame_array[i] = value
                print("i2c1 temp:", avg_temp)

    def ad7991_task():
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > AD7991_TASK_PERIOD:
                readings = ad7991.read_adc()
                # linpot_value.value = readings[0]  # TODO: re-enable if needed
                # adc1_value.value = readings[1]
                # adc2_value.value = readings[2]
                # adc3_value.value = readings[3]

                start_time = current_time
            else:
                time.sleep(TIME_1MS)

    def nau_task():
        """Continuously read linpot via NAU7802 at NAU7802_TASK_PERIOD rate."""
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > NAU7802_TASK_PERIOD:
                value_mm = read_linpot_mm(adc)
                if value_mm is not None:
                    linpot_reading.value = int(value_mm * 1000)  # Store as um in shared int
                    print(f"I2C1 linpot: {value_mm:.2f} mm")
                start_time = current_time
            else:
                time.sleep(TIME_1MS)

    mlx90640_thread = Thread(target=mlx90640_task)
    ad7991_thread = Thread(target=ad7991_task)
    nau_thread = Thread(target=nau_task)

    if mlx_enabled:
        mlx90640_thread.start()
    if ad7991_enabled:
        ad7991_thread.start()
    if nau_enabled:
        nau_thread.start()

    # Keep process alive
    while True:
        time.sleep(1)


# TODO: change config.txt make sure uart is enabled
def uart0_process(uart_serial, doppler_value):

    # TODO: init the ops243a = ops243a(dffsdf)

    def ops243a_task():
        while True:
            if uart_serial.in_waiting > 0:
                # TODO: init the class ride_height_value
                doppler_value.value = ops243a.read_rideheight()


if __name__ == "__main__":
    # --- Init I2C buses ---
    # I2C1: default Pi I2C (SCL/SDA on GPIO 2/3)
    i2c1_handle = busio.I2C(board.SCL, board.SDA)

    # I2C0: secondary bus (D1/D0 on GPIO 1/0)
    try:
        i2c0_handle = busio.I2C(board.D1, board.D0)
    except Exception as e:
        print(f"I2C0 init failed: {e}")
        i2c0_handle = None

    uart0_serial = serial.Serial(port="/dev/serial0", baudrate=19200, timeout=3.0)

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
        args=(i2c0_handle, avg_temp0_value, ir_frame0_update, ir_frame0_array, i2c0_linpot_reading)
    ) if i2c0_handle is not None else None

    i2c1_proc = Process(
        target=i2c1_process,
        args=(i2c1_handle, avg_temp1_value, ir_frame1_update, ir_frame1_array, i2c1_linpot_reading)
    )

    # Start all processes
    print("Starting CMR Data Acquisition System...")
    print(f"DAQ Pi ID: {DAQ_PI_ID}")

    if i2c0_proc is not None:
        i2c0_proc.start()
    else:
        print("I2C0 process skipped (bus not available)")

    i2c1_proc.start()

    while True:
        i2c0_mm = i2c0_linpot_reading.value / 1000.0
        i2c1_mm = i2c1_linpot_reading.value / 1000.0
        print(
            f"MAIN LOOP: Temp0: {avg_temp0_value.value}, "
            f"Temp1: {avg_temp1_value.value}, "
            f"Linpot I2C0: {i2c0_mm:.2f} mm, "
            f"Linpot I2C1: {i2c1_mm:.2f} mm"
        )
        time.sleep(0.5)
