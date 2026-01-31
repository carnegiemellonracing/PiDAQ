# Updated imports - removed deprecated sensors and CAN bus
from mlx90640.mlx90640 import MLX90640
from mlx90640_1.mlx90640_1 import MLX90640_1

from multiprocessing import Process, Queue, Value, Array
from smbus2 import SMBus
from threading import Thread
from datetime import datetime
# from random import randint

# from Utils.utils import test_id_is_active, extract_test_id

import os

import busio
import board
import serial
import RPi.GPIO as GPIO

import time

from pathlib import Path

# TODO: change way of doing this
if "DAQ_PI_ID" in os.environ:
    DAQ_PI_ID = int(os.getenv("DAQ_PI_ID"))
else:
    DAQ_PI_ID = 4

# Task timing constants
MLX90640_TASK_PERIOD = 0.125

# MLX90640 IR thermal camera
MLX90640_ADDRESS = 0x33
MLX90640_FRAME_RATE = 8.0

TIME_1MS = 0.001

LOG_DIRECTORY = str(Path(__file__).parent.absolute()) + "/../log/"


def i2c0_process(i2c_handle, avg_temp_value, ir_frame_update, ir_frame_array):
    #TODO: RTC code

    mlx_enabled = False

    try:
        mlx = MLX90640(i2c_handle, i2c_addr=MLX90640_ADDRESS, frame_rate=MLX90640_FRAME_RATE)
        mlx_enabled = True
    except Exception as e:
        print("MLX0 not detected")

    def mlx90640_task():
        while True:
            avg_temp, frame = mlx.read_frame()

            if avg_temp is not None:
                avg_temp_value.value = avg_temp
                
                #TODO: toggle with XOR
                if ir_frame_update.value == 0:
                    ir_frame_update.value = 1
                else:
                    ir_frame_update.value = 0
                
                for i, value in enumerate(frame):
                    ir_frame_array[i] = value
                
                print("i2c0 temp:", avg_temp)
    mlx90640_thread = Thread(target=mlx90640_task)
    
    if mlx_enabled:
        mlx90640_thread.start()

def i2c1_process(i2c_handle, avg_temp_value, ir_frame_update, ir_frame_array):
    
    mlx_enabled = False

    try:
        mlx = MLX90640_1(i2c_handle, i2c_addr=MLX90640_ADDRESS, frame_rate=MLX90640_FRAME_RATE)
        mlx_enabled = True
    except Exception as e:
        print("MLX1 not detected")

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
    
    mlx90640_thread = Thread(target=mlx90640_task)
    
    if mlx_enabled:
        mlx90640_thread.start()

if __name__ == "__main__":
    # Assigning the I2C buses
    i2c0_handle = SMBus(0)
    i2c1_handle = busio.I2C(board.SCL, board.SDA)

    # Shared values for inter-process communication
    avg_temp0_value = Value("i", 0)
    avg_temp1_value = Value("i", 0)
    ir_frame0_array = Array("i", 32 * 24)
    ir_frame1_array = Array("i", 32 * 24)
    ir_frame0_update = Value("b", 0)
    ir_frame1_update = Value("b", 0)
    
    # # UART sensor data
    # ride_height_value = Value("i", 0)  # UC5B20402 ultrasonic sensor
    # doppler_value = Value("i", 0)      # OPS243-A radar sensor
    
    # Test ID control (TODO: implement control mechanism - button/GPIO/network)
    # Previously received via CAN (0x777), now needs alternative input method
    test_id_value = Value("i", 0)

    # Create processes
    i2c0_process = Process(target=i2c0_process, args=(i2c0_handle, avg_temp0_value, ir_frame0_update, ir_frame0_array, ))
    i2c1_process = Process(target=i2c1_process, args=(i2c1_handle, avg_temp1_value, ir_frame1_update, ir_frame1_array, ))
    
    i2c0_process.start()
    i2c1_process.start()
    
    while True:
        print(f"MAIN LOOP: Temp 0:", {avg_temp0_value.value},", Temp 1:", avg_temp1_value.value)
    # uart_proc.start()
    # log_proc.start()
