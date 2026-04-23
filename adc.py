# nau7802_reader.py
# Reads strain gauge / load cell data from NAU7802 on Raspberry Pi Zero 2 W (I2C1)
# Install: pip3 install cedargrove-nau7802 adafruit-blinka

import time
import board
from cedargrove_nau7802 import NAU7802

# Initialize NAU7802 on default I2C bus (I2C1 on Pi)
i2c = board.I2C()  # Uses SCL (GPIO3) and SDA (GPIO2) on I2C1
nau7802 = NAU7802(i2c, address=0x2A, active_channels=1)


def zero_channel():
    """Calibrate the current channel. Remove all weight before calling."""
    print(f"Calibrating channel {nau7802.channel}...")
    cal_internal = nau7802.calibrate("INTERNAL")
    print(f"  INTERNAL calibration: {cal_internal}")
    cal_offset = nau7802.calibrate("OFFSET")
    print(f"  OFFSET calibration:   {cal_offset}")
    print(f"  Channel {nau7802.channel} zeroed.\n")


def read_raw(samples=10):
    """Read and average multiple raw samples."""
    total = 0
    for _ in range(samples):
        while not nau7802.available():
            pass
        total += nau7802.read()
    return total / samples


# --- Setup ---
print("NAU7802 Load Cell Reader")
print("=======================")

enabled = nau7802.enable(True)
print(f"Power enabled: {enabled}")

print("\n*** Remove all weight from the load cell! ***")
time.sleep(3)

nau7802.channel = 1
zero_channel()

# Store the zero offset for tare
zero_offset = read_raw(samples=20)
print(f"Zero offset: {zero_offset:.1f}\n")

# --- Main Loop ---
print("Reading... (Ctrl+C to stop)\n")
try:
    while True:
        raw = read_raw(samples=10)
        adjusted = raw - zero_offset
        print(f"Raw: {raw:>10.1f}  |  Tared: {adjusted:>10.1f}")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nDone.")
