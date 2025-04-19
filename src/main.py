from max11617.max11617 import MAX11617
from mlx90640.mlx90640 import MLX90640
from vl530l0x.vl530lx import VL53L0X

from multiprocessing import Process, Queue
from smbus2 import SMBus
from threading import Thread


import busio
import board

import time

I2C0_TASK_PERIOD = 0.125

VL530_TASK_PERIOD = 0.05
MAX11617_TASK_PERIOD = 0.005

MLX90640_ADDRESS = 0x33
MLX90640_FRAME_RATE = 8.0

VL53L0X_ADDRESS = 0x29

MAX11617_ADDRESS = 0x35
MAX11617_CHANNEL_COUNT = 3


def i2c0_process(i2c_handle, can_q):
    # TODO: Wrap in try catch
    mlx = MLX90640(i2c_handle, i2c_addr=MLX90640_ADDRESS, frame_rate=MLX90640_FRAME_RATE)

    start_time = time.time()    
    while True:
        current_time = time.time()
        if current_time - start_time > I2C0_TASK_PERIOD:
            avg_temperature, frame = mlx.read_frame()
            
            queue_data = []
            queue_data.append(("MLX", avg_temperature))
            queue_data.append(("I2C0", current_time - start_time))
            can_q.put(queue_data)
            
            start_time = current_time
        
        
def i2c1_process(i2c_handle, can_q):
    vl530 = VL53L0X(i2c_handle, VL53L0X_ADDRESS)
    max11617 = MAX11617(i2c_handle, MAX11617_ADDRESS, MAX11617_CHANNEL_COUNT)
    
    def vl530_task(can_q):
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > VL530_TASK_PERIOD:
                distance = vl530.read_distance()
                queue_data = []
                queue_data.append(("VL530", distance))
                queue_data.append(("I2C1_DISTANCE", current_time - start_time))
                can_q.put(queue_data)
                
                start_time = current_time
            else:
                time.sleep(0.001)
    
    def max11617_task(can_q):
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > MAX11617_TASK_PERIOD: 
                adc_data = max11617.read_adc()
                queue_data = []
                queue_data.append(("ADC0", adc_data[0]))
                queue_data.append(("ADC1", adc_data[1]))
                queue_data.append(("ADC2", adc_data[2]))
                queue_data.append(("I2C1_ADC", current_time - start_time))
                can_q.put(queue_data)
                
                start_time = current_time  
            else:
                time.sleep(0.001)
    
    vl530_thread = Thread(target=vl530_task, args=(can_q, ))
    max11617_thread = Thread(target=max11617_task, args=(can_q, ))
    
    vl530_thread.start()
    max11617_thread.start()


def can_process(can_q):
    # TODO: Implement MCP code
    
    while True:
        if not can_q.empty():
            queue_data = can_q.get()
            
            for data in queue_data:
                print(data)


if __name__ == "__main__":
    i2c0_handle = SMBus(0)
    i2c1_handle = busio.I2C(board.SCL, board.SDA)
    
    can_q = Queue()
    
    i2c0_process = Process(target=i2c0_process, args=(i2c0_handle,can_q,))
    i2c1_process = Process(target=i2c1_process, args=(i2c1_handle,can_q,))
    can_process = Process(target=can_process, args=(can_q,))
    i2c0_process.start()
    i2c1_process.start()
    can_process.start()