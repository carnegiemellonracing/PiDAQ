import spidev

from max11617.max11617 import MAX11617
from mlx90640.mlx90640 import MLX90640
from vl530l0x.vl530lx import VL53L0X
from mcp2515.mcp2515 import MCP2515

from multiprocessing import Process, Queue, Value
from smbus2 import SMBus
from threading import Thread, Lock

import os


import busio
import board

import time

DAQ_PI_ID = int(os.getenv("DAQ_PI_ID"))

MLX_CAN_ID = 0x660 + 16 * DAQ_PI_ID
ADC_CAN_ID = 0x661 + 16 * DAQ_PI_ID
VL_CAN_ID = 0x662 + 16 * DAQ_PI_ID

MLX90640_TASK_PERIOD = 0.125

VL530_TASK_PERIOD = 0.05
MAX11617_TASK_PERIOD = 0.005

MLX90640_ADDRESS = 0x33
MLX90640_FRAME_RATE = 8.0

VL53L0X_ADDRESS = 0x29

MAX11617_ADDRESS = 0x35
MAX11617_CHANNEL_COUNT = 3


def i2c0_process(i2c_handle, avg_temp_value):
    # TODO: Wrap in try catch
    mlx = MLX90640(i2c_handle, i2c_addr=MLX90640_ADDRESS, frame_rate=MLX90640_FRAME_RATE)

    start_time = time.time()    
    while True:
        current_time = time.time()
        if current_time - start_time > MLX90640_TASK_PERIOD:
            avg_temp_value.value, frame = mlx.read_frame()
            
            start_time = current_time
        
        
def i2c1_process(i2c_handle, distance_value, linpot_value, adc1_value, adc2_value):
    vl530 = VL53L0X(i2c_handle, VL53L0X_ADDRESS)
    max11617 = MAX11617(i2c_handle, MAX11617_ADDRESS, MAX11617_CHANNEL_COUNT)
    
    def vl530_task(distance_value):
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > VL530_TASK_PERIOD:
                distance_value.value = vl530.read_distance()
                
                start_time = current_time
            else:
                time.sleep(0.001)
    
    def max11617_task(linpot_value, adc1_value, adc2_value):
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > MAX11617_TASK_PERIOD: 
                linpot_value.value, adc1_value.value, adc2_value.value = max11617.read_adc()
                
                start_time = current_time  
            else:
                time.sleep(0.001)
    
    vl530_thread = Thread(target=vl530_task, args=(distance_value, ))
    max11617_thread = Thread(target=max11617_task, args=(linpot_value, adc1_value, adc2_value, ))
    
    vl530_thread.start()
    max11617_thread.start()


def can_process(spi_handle, avg_temp_value, distance_value, linpot_value, adc1_value, adc2_value):

    mcp = MCP2515(spi_handle, cs_pin=5)
    mcp.set_normal_mode()

    mcp_lock = Lock()

    def uint16_to_bytes(value):
        return [value & 0xFF, value >> 8]

    def max11617_task(mcp, linpot_value, adc1_value, adc2_value):
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
                time.sleep(0.001)

    def vl530_task(mcp, distance_value):
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > VL530_TASK_PERIOD:
                distance_bytes = uint16_to_bytes(distance_value.value)

                with mcp_lock:
                    mcp.send_message(can_id=VL_CAN_ID, data=distance_bytes)
                
                start_time = current_time
            else:
                time.sleep(0.001)

    def mlx90640_task(mcp, avg_temp_value):
        start_time = time.time()    
        while True:
            current_time = time.time()
            if current_time - start_time > MLX90640_TASK_PERIOD:
                avg_temp_bytes = uint16_to_bytes(avg_temp_value.value)

                with mcp_lock:
                    mcp.send_message(can_id=MLX_CAN_ID, data=avg_temp_bytes)
                
                start_time = current_time
            else:
                time.sleep(0.001)

    mlx90640_thread = Thread(target=mlx90640_task, args=(mcp, avg_temp_value, ))
    vl530_thread = Thread(target=vl530_task, args=(mcp, distance_value, ))
    max11617_thread = Thread(target=max11617_task, args=(mcp, linpot_value, adc1_value, adc2_value, ))

    mlx90640_thread.start()
    vl530_thread.start()
    max11617_thread.start()
    


if __name__ == "__main__":

    i2c0_handle = SMBus(0)

    i2c1_handle = busio.I2C(board.SCL, board.SDA)

    spi_handle = spidev.SpiDev()
    spi_handle.open(0, 0)
    spi_handle.max_speed_hz = 100000

    avg_temp_value = Value("i", 0)
    distance_value = Value("i", 0)
    linpot_value = Value("i", 0)
    adc1_value = Value("i", 0)
    adc2_value = Value("i", 0)

    i2c0_process = Process(target=i2c0_process, args=(i2c0_handle,avg_temp_value,))
    i2c1_process = Process(target=i2c1_process, args=(i2c1_handle,distance_value, linpot_value, adc1_value, adc2_value,))
    can_process = Process(target=can_process, args=(spi_handle, avg_temp_value, distance_value, linpot_value, adc1_value, adc2_value,))
    i2c0_process.start()
    i2c1_process.start()
    can_process.start()