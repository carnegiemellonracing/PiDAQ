import board
import busio
import adafruit_vl53l0x
import time
import numpy as np
from scipy.interpolate import interp1d

i2c = busio.I2C(board.D3, board.D2)
sensor = adafruit_vl53l0x.VL53L0X(i2c)
expectedValues = [
    50,
    55,
    60,
    65,
    70,
    75,
    80,
    85,
    90,
    95,
    100,
    105,
    110,
    115,
    120,
    125,
    130,
    135,
    140,
    145,
    150,
]
measuredValues = [
    68.5,
    73.8,
    77.5,
    84.1,
    88.6,
    92.3,
    95.2,
    97.9,
    100.5,
    102.9,
    101.1,
    107.6,
    114.3,
    121.2,
    138.5,
    143.5,
    150,
    152.5,
    152.5,
    156.5,
    161,
]

calibrationFunction = interp1d(
    measuredValues, expectedValues, kind="linear", fill_value="extrapolate"
)


def read_range():
    calibrationFunction(sensor.range)


while 1:
    print(f"calibratedValue = {read_range()}")
    time.sleep(0.01)
