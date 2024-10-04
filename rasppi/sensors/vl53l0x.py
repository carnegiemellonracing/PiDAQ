import adafruit_vl53l0x
import time


def init_vl53l0x(i2c):
    sensor = adafruit_vl53l0x.VL53L0X(i2c)
    print('vl53l0x connected!')
    return sensor


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

def read_range(sensor):
    return sensor.range


def main():
    while 1:
        print(f"calibratedValue = {read_range()}")
        time.sleep(0.01)


if __name__ == "__main__":
    main()
