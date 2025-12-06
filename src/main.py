# REMOVE - No longer using SPI for CAN
import spidev  # <-- REMOVE THIS

# REPLACE - Change to AD7991 driver
from max11617.max11617 import MAX11617  # <-- REPLACE with: from ad7991.ad7991 import AD7991
from mlx90640.mlx90640 import MLX90640
# REPLACE - Change to new UART ride height sensors (UC5B20402 and OPS243-A)
from vl530l0x.vl530lx import VL53L0X  # <-- REMOVE THIS (VL53L0X no longer used)
# REMOVE - CAN controller no longer used
from mcp2515.mcp2515 import MCP2515  # <-- REMOVE THIS

from multiprocessing import Process, Queue, Value, Array
from smbus2 import SMBus
from threading import Thread, Lock  # <-- Lock can be removed after CAN is deleted
from datetime import datetime
from random import randint

# UNCOMMENT - Use utility functions from utils.py
#from Utils.utils import uint16_to_bytes, bytes_to_uint16, test_id_is_active, extract_test_id  # <-- UNCOMMENT THIS

import os

import busio
import board

import time

from pathlib import Path


if "DAQ_PI_ID" in os.environ:
    DAQ_PI_ID = int(os.getenv("DAQ_PI_ID"))
else:
    DAQ_PI_ID = 4

# REMOVE - CAN ID definitions no longer needed
MLX_CAN_ID = 0x660 + 16 * DAQ_PI_ID  # <-- REMOVE (was for CAN transmission)
ADC_CAN_ID = 0x661 + 16 * DAQ_PI_ID  # <-- REMOVE (was for CAN transmission)
VL_CAN_ID = 0x662 + 16 * DAQ_PI_ID   # <-- REMOVE (was for CAN transmission)

MLX90640_TASK_PERIOD = 0.125

# REMOVE - VL530 no longer used
VL530_TASK_PERIOD = 0.05  # <-- REMOVE THIS
# UPDATE - Change to AD7991_TASK_PERIOD (and may need different timing)
MAX11617_TASK_PERIOD = 0.005  # <-- RENAME to AD7991_TASK_PERIOD

MLX90640_ADDRESS = 0x33
MLX90640_FRAME_RATE = 8.0

# REMOVE - VL53L0X no longer used
VL53L0X_ADDRESS = 0x29  # <-- REMOVE THIS

# UPDATE - Change to AD7991 address and channel count
MAX11617_ADDRESS = 0x35  # <-- UPDATE to AD7991_ADDRESS (check datasheet for correct address)
MAX11617_CHANNEL_COUNT = 3  # <-- UPDATE to AD7991_CHANNEL_COUNT = 4

TIME_1MS = 0.001
# REMOVE - SPI settings no longer needed
SPI_MAX_SPEED_HZ = 100000  # <-- REMOVE THIS
MCP_CS_PIN = 5  # <-- REMOVE THIS

LOG_DIRECTORY = str(Path(__file__).parent.absolute()) + "/../log/"


def i2c0_process(i2c_handle, avg_temp_value, ir_frame_update, ir_frame_array):
    
    mlx_enabled = False
    
    try:    
        mlx = MLX90640(i2c_handle, i2c_addr=MLX90640_ADDRESS, frame_rate=MLX90640_FRAME_RATE)
        mlx_enabled = True
    except Exception as e:
        print("MLX not detected")

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
                    
    mlx90640_thread = Thread(target=mlx90640_task)
    
    if mlx_enabled:
        mlx90640_thread.start()

        
# NEEDS MAJOR UPDATES - Replace VL53L0X and MAX11617 with new sensors (ASK JASMINE FOR CLARIFICATION)
# CHANGES TO BE MADE 
# - Add MLX tire sensor to this i2c
# - Add new ADC to this i2c
def i2c1_process(i2c_handle, distance_value, linpot_value, adc1_value, adc2_value):
    
    # REMOVE - VL530 no longer used (replaced by UC5B20402 and OPS243-A on UART)
    vl530_enabled = False  # <-- REMOVE THIS SECTION
    max11617_enabled = False  # <-- RENAME to ad7991_enabled
    
    # REMOVE ENTIRE TRY/EXCEPT BLOCK - VL530 no longer used
    try:
        vl530 = VL53L0X(i2c_handle, VL53L0X_ADDRESS)
        vl530_enabled = True
    except Exception as e:
        print("VL530 not detected")
    # <-- END REMOVE
        
    # UPDATE - Replace with AD7991 initialization
    try:
        max11617 = MAX11617(i2c_handle, MAX11617_ADDRESS, MAX11617_CHANNEL_COUNT)  # <-- REPLACE with AD7991
        max11617_enabled = True  # <-- RENAME to ad7991_enabled
    except Exception as e:
        print("MAX11617 not detected")  # <-- UPDATE message to "AD7991 not detected"
    
    #------------------------------------------------#
    # REMOVE ENTIRE FUNCTION - VL530 replaced by UART sensors
    def vl530_task():
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > VL530_TASK_PERIOD:
                distance_value.value = vl530.read_distance()
                
                start_time = current_time
            else:
                time.sleep(TIME_1MS)
    #------------------------------------------------#
    
    #------------------------------------------------#
    # UPDATE - Modify for AD7991 (4 channels instead of 3)
    def max11617_task():  # <-- RENAME to ad7991_task
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > MAX11617_TASK_PERIOD:  # <-- UPDATE to AD7991_TASK_PERIOD
                linpot_value.value, adc1_value.value, adc2_value.value = max11617.read_adc()  # <-- ADD adc3_value.value
                
                start_time = current_time  
            else:
                time.sleep(TIME_1MS)
    #------------------------------------------------#
    
    # REMOVE - vl530_thread no longer needed
    vl530_thread = Thread(target=vl530_task)  # <-- REMOVE THIS
    max11617_thread = Thread(target=max11617_task)  # <-- RENAME to ad7991_thread
    
    # REMOVE - vl530 thread start
    if vl530_enabled:  # <-- REMOVE THIS ENTIRE IF BLOCK
        vl530_thread.start()
        
    if max11617_enabled:  # <-- RENAME to ad7991_enabled
        max11617_thread.start()  # <-- RENAME to ad7991_thread.start()

#Added utility functions to a different file to clean up a bit, just need to replace them in here
#_test_active(test_id) -> test_id_is_active(test_id)
#_extract_id(test_id) -> extract_test_id(test_id)
# NEEDS UPDATES - Should log ALL sensor data, not just IR frames
# To Dos: Add parameters for all sensor values: distance, linpot, adc1, adc2, adc3, ride_height, doppler, etc.
def log_process(ir_frame_update, ir_frame_array, test_id_value):
    
    os.makedirs(LOG_DIRECTORY, exist_ok=True)

    file_handle = None
    current_test_id = 0
    last_update_value = 0
   
    # REPLACE - Use utility functions from utils.py instead
    def _test_active(test_id):  # <-- REPLACE with: from Utils.utils import test_id_is_active
        return test_id >= 2 ** 15 
    
    def _extract_id(test_id):  # <-- REPLACE with: from Utils.utils import extract_test_id
        return test_id & 0x7FFF
    
    while True:
       # Check active
        test_active = _test_active(test_id_value.value)
        test_id = _extract_id(test_id_value.value)

        # Generate file handles        
        if test_id != current_test_id:
            current_test_id = test_id
            if file_handle is not None:
                file_handle.close()
            file_handle = None
            
            if test_active:
                time_in_min = datetime.now().strftime("%Y-%m-%d_%H:%M")
                file_handle = open(f"{LOG_DIRECTORY}/{time_in_min}_{test_id}.log", "w")
        
        if test_active:
            # Log MLX90640 data
            if (ir_frame_update.value != last_update_value):
                timestamp_str = datetime.now().strftime("%H:%M:%S.%f")
                file_handle.write(timestamp_str + " ; ")
                
                file_handle.write(f"{test_id_value.value & 0x7FFF} ; ")
                
                for value in ir_frame_array:
                    file_handle.write(f"{value},")
                file_handle.write("\n")
                                
                last_update_value = ir_frame_update.value
        
        time.sleep(TIME_1MS)
    
#COMPLETELY REMOVE THIS ENTIRE FUNCTION (Lines 189-271)
#---------------------------------------------------------------#
# The can_process function is no longer needed because:
# 1. CAN bus communication has been removed from hardware
# 2. Data logging is handled by log_process (just needs expansion)
# 3. uint16_to_bytes conversion moved to Utils/utils.py
# 4. test_id is no longer received from CAN (need alternative method)
#
# DELETE EVERYTHING FROM HERE...
def can_process(spi_handle, avg_temp_value, distance_value, linpot_value, adc1_value, adc2_value, test_id_value):

    mcp = MCP2515(spi_handle, cs_pin=MCP_CS_PIN)
    mcp.set_config_mode()
    mcp.enable_filters(0, True) 
    mcp.enable_filters(1, False)
    mcp.set_acceptance_mask(0, 0x7FF)
    mcp.set_acceptance_filter(0, 0x777)  
    mcp.set_normal_mode()

    mcp_lock = Lock()

    def uint16_to_bytes(value):
        return [value & 0xFF, value >> 8]

    def max11617_task():
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > MAX11617_TASK_PERIOD: 
                linpot_bytes = uint16_to_bytes(linpot_value.value)
                adc1_bytes = uint16_to_bytes(adc1_value.value)
                adc2_bytes = uint16_to_bytes(adc2_value.value)

                can_data = linpot_bytes + adc1_bytes + adc2_bytes

                with mcp_lock:
                    mcp.send_message(can_id=ADC_CAN_ID, data=can_data)
                
                start_time = current_time  
            else:
                time.sleep(TIME_1MS)

    def vl530_task():
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > VL530_TASK_PERIOD:
                distance_bytes = uint16_to_bytes(distance_value.value)

                with mcp_lock:
                    mcp.send_message(can_id=VL_CAN_ID, data=distance_bytes)
                
                start_time = current_time
            else:
                time.sleep(TIME_1MS)

    def mlx90640_task():
        start_time = time.time()    
        while True:
            current_time = time.time()
            if current_time - start_time > MLX90640_TASK_PERIOD:
                avg_temp_bytes = uint16_to_bytes(avg_temp_value.value)

                with mcp_lock:
                    mcp.send_message(can_id=MLX_CAN_ID, data=avg_temp_bytes)
                
                start_time = current_time
            else:
                time.sleep(TIME_1MS)
                
    def read_task():
        while True:
            with mcp_lock:
                can_id, can_data, can_length = mcp.read_message()
            
            if can_id is not None:
                if can_id == 0x777 and can_length == 2:
                    test_id_value.value = (can_data[1] << 8) + can_data[0]
            
            time.sleep(TIME_1MS)


    mlx90640_thread = Thread(target=mlx90640_task)
    vl530_thread = Thread(target=vl530_task)
    max11617_thread = Thread(target=max11617_task)
    read_thread = Thread(target=read_task)

    mlx90640_thread.start()
    vl530_thread.start()
    max11617_thread.start()
    read_thread.start()   
# ...TO HERE (End of can_process deletion)
#---------------------------------------------------------------#


if __name__ == "__main__":

    i2c0_handle = SMBus(0)

    i2c1_handle = busio.I2C(board.SCL, board.SDA)

    # REMOVE - SPI no longer used (CAN removed)
    spi_handle = spidev.SpiDev()  # <-- REMOVE THESE 3 LINES
    spi_handle.open(0, 0)
    spi_handle.max_speed_hz = SPI_MAX_SPEED_HZ

    avg_temp_value = Value("i", 0)
    ir_frame_array = Array("i", 32 * 24)
    ir_frame_update = Value("b", 0)
    
    # UPDATE - distance_value may no longer be needed (VL530 removed, replaced by UART sensors)
    distance_value = Value("i", 0)  # <-- MAY NEED TO REPLACE with ride_height_value and doppler_value
    
    linpot_value = Value("i", 0)
    adc1_value = Value("i", 0)
    adc2_value = Value("i", 0)
    # ADD - Need adc3_value for 4th ADC channel
    # adc3_value = Value("i", 0)  # <-- ADD THIS
    
    # UPDATE - test_id_value was received from CAN (0x777), need alternative method to set this
    test_id_value = Value("i", 0)  # <-- Need new way to control test_id (button? config file? network?)

    i2c0_process = Process(target=i2c0_process, args=(i2c0_handle, avg_temp_value, ir_frame_update, ir_frame_array, ))
    # UPDATE - i2c1_process needs adc3_value added to args, and distance_value may be removed
    i2c1_process = Process(target=i2c1_process, args=(i2c1_handle, distance_value, linpot_value, adc1_value, adc2_value,))

    #REMOVE THIS!
    can_process = Process(target=can_process, args=(spi_handle, avg_temp_value, distance_value, linpot_value, adc1_value, adc2_value,test_id_value,))  # <-- DELETE THIS LINE
    #REMOVE THIS!

    # UPDATE - log_process needs expanded args to log ALL sensor data
    log_process = Process(target=log_process, args=(ir_frame_update, ir_frame_array,test_id_value,))
    
    i2c0_process.start()
    i2c1_process.start()
    can_process.start()  # <-- REMOVE THIS LINE
    log_process.start()
