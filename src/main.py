import spidev

from max11617.max11617 import MAX11617
from mlx90640.mlx90640 import MLX90640
from vl530l0x.vl530lx import VL53L0X
from mcp2515.mcp2515 import MCP2515

from multiprocessing import Process, Queue, Value, Array
from smbus2 import SMBus
from threading import Thread, Lock
from datetime import datetime
from random import randint

import os

import busio
import board

import time

from pathlib import Path


if "DAQ_PI_ID" in os.environ:
    DAQ_PI_ID = int(os.getenv("DAQ_PI_ID"))
else:
    DAQ_PI_ID = 4

MLX_CAN_ID = 0x660 + 16 * DAQ_PI_ID # 16 bc we do 660 for pi0, 670 for pi1... (in hex, 16 apart)
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

TIME_1MS = 0.001
SPI_MAX_SPEED_HZ = 100000
MCP_CS_PIN = 5 # this is the chip select pin (designated by the chosen GPIO on PI)

LOG_DIRECTORY = str(Path(__file__).parent.absolute()) + "/../log/"


class KalmanCV:
	"""
	State vector: [position, velocity]. Measurement: position only.
	Tuning parameters:
	- measurement_variance (R): variance of VL53L0X measurement noise [mm^2]
	- acceleration_variance (sigma_a2): variance of white acceleration [mm^2/s^4]
	"""

	def __init__(self,
				 initial_position: float,
				 initial_velocity: float,
				 measurement_variance: float,
				 acceleration_variance: float,
				 initial_position_variance: float = 1e6,
				 initial_velocity_variance: float = 1e6) -> None:
		# State estimates
		self.x = float(initial_position)
		self.v = float(initial_velocity)
		# Covariance matrix P elements
		self.P11 = float(initial_position_variance)
		self.P12 = 0.0
		self.P21 = 0.0
		self.P22 = float(initial_velocity_variance)
		# Noise parameters
		self.R = float(measurement_variance)
		self.sigma_a2 = float(acceleration_variance)

	def predict(self, dt: float) -> None:
		"""Time update with variable dt. O(1)."""
		# State transition: x <- x + v*dt; v unchanged under constant-velocity
		self.x = self.x + self.v * dt
		# P <- F P F^T + Q(dt), where F = [[1, dt], [0, 1]]
		P11 = self.P11
		P12 = self.P12
		P21 = self.P21
		P22 = self.P22
		# F P
		FP11 = P11 + dt * P21
		FP12 = P12 + dt * P22
		FP21 = P21
		FP22 = P22
		# (F P) F^T
		P11_new = FP11 + dt * FP12
		P12_new = FP12
		P21_new = FP21 + dt * FP22
		P22_new = FP22
		# Process noise for constant acceleration model
		dt2 = dt * dt
		dt3 = dt2 * dt
		dt4 = dt2 * dt2
		q11 = 0.25 * dt4 * self.sigma_a2
		q12 = 0.5 * dt3 * self.sigma_a2
		q22 = dt2 * self.sigma_a2
		self.P11 = P11_new + q11
		self.P12 = P12_new + q12
		self.P21 = P21_new + q12
		self.P22 = P22_new + q22

	def update(self, z: float) -> None:
		"""Measurement update using position-only measurement. O(1)."""
		# Innovation
		y = float(z) - self.x
		# Residual covariance S = H P H^T + R = P11 + R
		S = self.P11 + self.R
		# Kalman gain K = P H^T S^{-1} -> [P11/S, P21/S]^T
		K1 = self.P11 / S
		K2 = self.P21 / S
		# State update
		self.x = self.x + K1 * y
		self.v = self.v + K2 * y
		# Covariance update: P <- (I - K H) P, with H = [1, 0]
		P11_old = self.P11
		P12_old = self.P12
		P21_old = self.P21
		P22_old = self.P22
		self.P11 = (1.0 - K1) * P11_old
		self.P12 = (1.0 - K1) * P12_old
		self.P21 = P21_old - K2 * P11_old
		self.P22 = P22_old - K2 * P12_old


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

        
def i2c1_process(i2c_handle, distance_value, linpot_value, adc1_value, adc2_value):
    
    vl530_enabled = False
    max11617_enabled = False
    
    try:
        vl530 = VL53L0X(i2c_handle, VL53L0X_ADDRESS)
        vl530_enabled = True
    except Exception as e:
        print("VL530 not detected")
        
    try:
        max11617 = MAX11617(i2c_handle, MAX11617_ADDRESS, MAX11617_CHANNEL_COUNT)
        max11617_enabled = True
    except Exception as e:
        print("MAX11617 not detected")
    
    def vl530_task():
        # Initialize filter using a first measurement
        last_t = time.time()
        first_distance = vl530.read_distance()
        # Tuning: R ~ measurement noise variance (mm^2), sigma_a2 ~ white accel variance (mm^2/s^4)
        kf = KalmanCV(
            initial_position=first_distance,
            initial_velocity=0.0,
            measurement_variance=400.0,
            acceleration_variance=2500.0,
            initial_position_variance=1e4,
            initial_velocity_variance=1e4,
        )
        distance_value.value = int(first_distance)

        start_time = last_t
        while True:
            current_time = time.time()
            if current_time - start_time > VL530_TASK_PERIOD:
                dt = max(0.0, current_time - last_t)
                last_t = current_time

                kf.predict(dt)  # O(1)
                z = vl530.read_distance()
                kf.update(z)    # O(1)
                distance_value.value = int(kf.x)

                start_time = current_time
            else:
                time.sleep(TIME_1MS)
    
    def max11617_task():
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > MAX11617_TASK_PERIOD: 
                linpot_value.value, adc1_value.value, adc2_value.value = max11617.read_adc()
                
                start_time = current_time  
            else:
                time.sleep(TIME_1MS)
    
    vl530_thread = Thread(target=vl530_task)
    max11617_thread = Thread(target=max11617_task)
    
    if vl530_enabled:
        vl530_thread.start()
        
    if max11617_enabled:
        max11617_thread.start()


def log_process(ir_frame_update, ir_frame_array, test_id_value):
    
    os.makedirs(LOG_DIRECTORY, exist_ok=True)

    file_handle = None
    current_test_id = 0
    last_update_value = 0
   
    def _test_active(test_id):
        return test_id >= 2 ** 15 
    
    def _extract_id(test_id):
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


if __name__ == "__main__":

    i2c0_handle = SMBus(0)

    i2c1_handle = busio.I2C(board.SCL, board.SDA)

    spi_handle = spidev.SpiDev()
    spi_handle.open(0, 0)
    spi_handle.max_speed_hz = SPI_MAX_SPEED_HZ

    avg_temp_value = Value("i", 0)
    ir_frame_array = Array("i", 32 * 24)
    ir_frame_update = Value("b", 0)
    
    distance_value = Value("i", 0)
    
    linpot_value = Value("i", 0)
    adc1_value = Value("i", 0)
    adc2_value = Value("i", 0)
    
    test_id_value = Value("i", 0)

    i2c0_process = Process(target=i2c0_process, args=(i2c0_handle, avg_temp_value, ir_frame_update, ir_frame_array, ))
    i2c1_process = Process(target=i2c1_process, args=(i2c1_handle, distance_value, linpot_value, adc1_value, adc2_value,))
    can_process = Process(target=can_process, args=(spi_handle, avg_temp_value, distance_value, linpot_value, adc1_value, adc2_value,test_id_value,))
    log_process = Process(target=log_process, args=(ir_frame_update, ir_frame_array,test_id_value,))
    
    i2c0_process.start()
    i2c1_process.start()
    can_process.start()
    log_process.start()
