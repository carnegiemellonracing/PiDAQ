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

from pathlib import Path

# TODO: change way of doing this
if "DAQ_PI_ID" in os.environ:
    DAQ_PI_ID = int(os.getenv("DAQ_PI_ID"))
else:
    DAQ_PI_ID = 4

# Task timing constants
MLX90640_TASK_PERIOD = 0.125
AD7991_TASK_PERIOD = 0.005

# MLX90640 IR thermal camera
MLX90640_ADDRESS = 0x33
MLX90640_FRAME_RATE = 8.0

# AD7991 ADC (4-channel 12-bit ADC)
AD7991_ADDRESS = 0x28  # AD7991-0 address, if -0 then 0x29
AD7991_CHANNEL_COUNT = 4

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

def i2c1_process(i2c_handle, avg_temp_value, ir_frame_update, ir_frame_array,
                 linpot_value, adc1_value, adc2_value, adc3_value):
    
    mlx_enabled = False
    ad7991_enabled = False

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
                linpot_value.value = ad7991.read_adc()[0]
                adc1_value.value = ad7991.read_adc()[1]
                adc2_value.value = ad7991.read_adc()[2]
                adc3_value.value = ad7991.read_adc()[3]
                
                start_time = current_time  
            else:
                time.sleep(TIME_1MS)
    
    mlx90640_thread = Thread(target=mlx90640_task)
    ad7991_thread = Thread(target=ad7991_task)
    
    if mlx_enabled:
        mlx90640_thread.start()
    if ad7991_enabled:
        ad7991_thread.start()

#TODO: change config.txt make sure uart is enabled
def uart0_process(uart_serial, doppler_value):

    #TODO: init the ops243a = ops243a(dffsdf)

    def ops243a_task():
        while True:
            if uart_serial.in_waiting > 0:
                #TODO: init the class ride_height_value
                doppler_value.value = ops243a.read_rideheight()





# def uart_process(ride_height_value, doppler_value):
#     """
#     UART Process - Handles UART-based sensors
#     - UC5B20402: Ultrasonic ride height sensor (Software UART)
#     - OPS243-A: Doppler radar sensor (Pi UART)
    
#     TODO: Implement sensor initialization and reading
#     """
#     ride_height_enabled = False
#     doppler_enabled = False
    
#     # TODO: Initialize UC5B20402 ride height sensor
#     # try:
#     #     ride_height_sensor = UC5B20402(uart_port=..., baudrate=...)
#     #     ride_height_enabled = True
#     #     print("UC5B20402 ride height sensor initialized")
#     # except Exception as e:
#     #     print(f"UC5B20402 not detected: {e}")
    
#     # Initialize OPS243-A doppler sensor (uncomment when ready)
#     # try:
#     #     from ops243a.ops243a import OPS243A
#     #     doppler_sensor = OPS243A('/dev/ttyAMA0')
#     #     doppler_enabled = True
#     #     print("OPS243-A doppler sensor initialized")
#     # except Exception as e:
#     #     print(f"OPS243-A not detected: {e}")
    
#     def ride_height_task():
#         """Reads ride height sensor at specified rate"""
#         RIDE_HEIGHT_TASK_PERIOD = 0.02  # 50 Hz
#         start_time = time.time()
#         while True:
#             current_time = time.time()
#             if current_time - start_time > RIDE_HEIGHT_TASK_PERIOD:
#                 # TODO: Read ride height sensor
#                 # ride_height_value.value = ride_height_sensor.read()
                
#                 start_time = current_time
#             else:
#                 time.sleep(TIME_1MS)
    
#     def doppler_task():
#         """Reads doppler sensor at 100 Hz"""
#         DOPPLER_TASK_PERIOD = 0.01  # 100 Hz
#         start_time = time.time()
#         while True:
#             current_time = time.time()
#             if current_time - start_time > DOPPLER_TASK_PERIOD:
#                 # Read speed in m/s and convert to integer (cm/s * 100)
#                 speed = doppler_sensor.read_speed()
#                 doppler_value.value = int(speed * 100)
                
#                 start_time = current_time
#             else:
#                 time.sleep(TIME_1MS)
    
#     # TODO: Uncomment when sensors are implemented
#     # ride_height_thread = Thread(target=ride_height_task)
#     # doppler_thread = Thread(target=doppler_task)
    
#     # if ride_height_enabled:
#     #     ride_height_thread.start()
    
#     # if doppler_enabled:
#     #     doppler_thread.start()
    
#     # Placeholder - keep process alive
#     while True:
#         time.sleep(1)




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
    uart0_serial = serial.Serial(port="/dev/serial0", baudrate=19200, timeout=3.0)

    # Shared values for inter-process communication
    avg_temp0_value = Value("i", 0)
    avg_temp1_value = Value("i", 0)
    ir_frame0_array = Array("i", 32 * 24)
    ir_frame1_array = Array("i", 32 * 24)
    ir_frame0_update = Value("b", 0)
    ir_frame1_update = Value("b", 0)
    
    linpot_value = Value("i", 0)
    adc1_value = Value("i", 0)
    adc2_value = Value("i", 0)
    adc3_value = Value("i", 0)
    
    # # UART sensor data
    # ride_height_value = Value("i", 0)  # UC5B20402 ultrasonic sensor
    # doppler_value = Value("i", 0)      # OPS243-A radar sensor
    
    # Test ID control (TODO: implement control mechanism - button/GPIO/network)
    # Previously received via CAN (0x777), now needs alternative input method
    test_id_value = Value("i", 0)

    # Create processes
    i2c0_process = Process(target=i2c0_process, args=(i2c0_handle, avg_temp0_value, ir_frame0_update, ir_frame0_array, ))
    i2c1_process = Process(target=i2c1_process, args=(i2c1_handle, avg_temp1_value, ir_frame1_update, ir_frame1_array, 
                                                      linpot_value, adc1_value, adc2_value,adc3_value, ))
    # uart0_process = Process(target=uart0_process, args=(uart0_serial, doppler_value))        
    
    
    
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
    
    while True:
        print(f"MAIN LOOP: Temp 0:", {avg_temp0_value.value},", Temp 1:", avg_temp1_value.value)
    # uart_proc.start()
    # log_proc.start()
