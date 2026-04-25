# Updated imports - removed deprecated sensors and CAN bus
from max11617.max11617 import MAX11617  # Using MAX11617 driver for AD7991 ADC
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
import csv
import subprocess

from pathlib import Path

# TODO: change way of doing this
if "DAQ_PI_ID" in os.environ:
    DAQ_PI_ID = int(os.getenv("DAQ_PI_ID"))
else:
    DAQ_PI_ID = 4

# Task timing constants
MLX90640_TASK_PERIOD = 0.125
MAX11617_TASK_PERIOD = 0.005

# MLX90640 IR thermal camera
MLX90640_ADDRESS = 0x33
MLX90640_FRAME_RATE = 8.0

# MAX11617 ADC
MAX11617_ADDRESS = 0x35
MAX11617_CHANNEL_COUNT = 3

TIME_1MS = 0.001

LOG_DIRECTORY = str(Path(__file__).parent.absolute()) + "/../log/"
LAST_GOOD_TIME_FILE = "last_good_time.txt"


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
                
                #print("i2c0 temp:", avg_temp)
    mlx90640_thread = Thread(target=mlx90640_task)
    
    if mlx_enabled:
        mlx90640_thread.start()

def i2c1_process(i2c_handle, avg_temp_value, ir_frame_update, ir_frame_array,
                 RL_linpot_value, RR_linpot_value):
    
    mlx_enabled = False
    max11617_enabled = False

    try:
        mlx = MLX90640_1(i2c_handle, i2c_addr=MLX90640_ADDRESS, frame_rate=MLX90640_FRAME_RATE)
        mlx_enabled = True
    except Exception as e:
        print("MLX1 not detected")

    try:
        max11617 = MAX11617(i2c_handle, MAX11617_ADDRESS, MAX11617_CHANNEL_COUNT)
        max11617_enabled = True
    except Exception as e:
        print(f"MAX11617 (ADC) not detected")

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
                #print("i2c1 temp:", avg_temp)
    def max11617_task():
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > MAX11617_TASK_PERIOD:
                RR_linpot_value.value = max11617.read_adc()[0]
                RL_linpot_value.value = max11617.read_adc()[1]

                start_time = current_time  
            else:
                time.sleep(TIME_1MS)
    
    mlx90640_thread = Thread(target=mlx90640_task)
    max11617_thread = Thread(target=max11617_task)
    
    if mlx_enabled:
        mlx90640_thread.start()
    if max11617_enabled:
        max11617_thread.start()

def log_process(avg_temp0_value, ir_frame0_update, ir_frame0_array,
                avg_temp1_value, ir_frame1_update, ir_frame1_array,
                RL_linpot_value, RR_linpot_value):

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
        "RL_linpot",
        "RR_linpot"
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
                RL_linpot_value.value,
                RR_linpot_value.value
            ])

            file_handle.flush()
            last_update_value = ir_frame0_update.value

        time.sleep(0.001)
    
    

# def log_process(ir_frame_update, ir_frame_array, test_id_value, avg_temp_value, 
#                 linpot_value, adc1_value, adc2_value, adc3_value, 
#                 ride_height_value, doppler_value):

#     # Logging process - Writes all sensor data to Pi memory (/log directory)
#     #------------------------------------------------------------------------#
#     # Logs:
#     # - MLX90640: IR frame (768 pixels) + average temperature
#     # - AD7991: 4 ADC channels (linpot, adc1, adc2, adc3)
#     # - UC5B20402: Ride height (ultrasonic distance)
#     # - OPS243-A: Doppler radar (velocity/speed)
    
#     # File format: CSV with timestamp, test_id, sensor data
#     #------------------------------------------------------------------------#

#     os.makedirs(LOG_DIRECTORY, exist_ok=True)

#     file_handle = None
#     current_test_id = 0
#     last_update_value = 0
    
#     while True:
#         # Check if test is active using utility functions
#         test_active = test_id_is_active(test_id_value.value)
#         test_id = extract_test_id(test_id_value.value)

#         # Generate file handles when test ID changes
#         if test_id != current_test_id:
#             current_test_id = test_id
#             if file_handle is not None:
#                 file_handle.close()
#             file_handle = None
            
#             if test_active:
#                 time_in_min = datetime.now().strftime("%Y-%m-%d_%H:%M")
#                 file_handle = open(f"{LOG_DIRECTORY}/{time_in_min}_{test_id}.log", "w")
#                 # Write CSV header
#                 file_handle.write("timestamp,test_id,avg_temp,linpot,adc1,adc2,adc3,ride_height,doppler,ir_frame\n")
        
#         if test_active and file_handle is not None:
#             # Log all sensor data when IR frame updates (triggers at MLX frame rate)
#             if (ir_frame_update.value != last_update_value):
#                 timestamp_str = datetime.now().strftime("%H:%M:%S.%f")
                
#                 # CSV format: timestamp, test_id, avg_temp, ADCs, UART sensors, ir_frame
#                 file_handle.write(f"{timestamp_str},")
#                 file_handle.write(f"{test_id},")
#                 file_handle.write(f"{avg_temp_value.value},")
#                 file_handle.write(f"{linpot_value.value},")
#                 file_handle.write(f"{adc1_value.value},")
#                 file_handle.write(f"{adc2_value.value},")
#                 file_handle.write(f"{adc3_value.value},")
#                 file_handle.write(f"{ride_height_value.value},")
#                 file_handle.write(f"{doppler_value.value},")
                
#                 for i, value in enumerate(ir_frame_array):
#                     file_handle.write(f"{value}")
#                     if i < len(ir_frame_array) - 1:
#                         file_handle.write(",")
#                 file_handle.write("\n")
#                 file_handle.flush()  # Ensure data is written immediately
                                
#                 last_update_value = ir_frame_update.value
        
#         time.sleep(TIME_1MS)


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
    
    RL_linpot_value = Value("i", 0)
    RR_linpot_value = Value("i", 0)
    
    # Test ID control (TODO: implement control mechanism - button/GPIO/network)
    # Previously received via CAN (0x777), now needs alternative input method
    test_id_value = Value("i", 0)

    # Create processes
    i2c0_process = Process(target=i2c0_process, args=(i2c0_handle, avg_temp0_value, ir_frame0_update, ir_frame0_array, ))
    i2c1_process = Process(target=i2c1_process, args=(i2c1_handle, avg_temp1_value, ir_frame1_update, ir_frame1_array, 
                                                      RL_linpot_value, RR_linpot_value,))
    log_process = Process(target=log_process, args=(avg_temp0_value, ir_frame0_update, ir_frame0_array, avg_temp1_value, 
                ir_frame1_update, ir_frame1_array, RL_linpot_value, RR_linpot_value,))
    
    # log_proc = Process(target=log_process, 
    #                    args=(ir_frame_update, ir_frame_array, test_id_value, avg_temp_value,
    #                          linpot_value, adc1_value, adc2_value, adc3_value,
    #                          ride_height_value, doppler_value))
    
    # Start all processes
    # print("Starting CMR Data Acquisition System...")
    # print(f"DAQ Pi ID: {DAQ_PI_ID}")
    # print(f"Log directory: {LOG_DIRECTORY}")
    
    i2c0_process.start()
    i2c1_process.start()
    log_process.start()
    
    while True:
        print(f"MAIN LOOP: Temp 0:", {avg_temp0_value.value},", Temp 1:", avg_temp1_value.value, ", Linpot:", RL_linpot_value.value, RR_linpot_value.value)
    # log_proc.start()
