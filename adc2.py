# nau7802_single_ended.py
# Single-ended ADC reading on Raspberry Pi Zero 2 W (I2C1)
# Signal wired to A+, A- tied to GND, E+/E- unused
# Install: pip3 install cedargrove-nau7802 adafruit-blinka

import time
import board
from cedargrove_nau7802 import NAU7802
from smbus2 import SMBus


#i2c = board.I2C()
i2c = SMBus(0)
nau7802 = NAU7802(i2c, address=0x2A, active_channels=1)

nau7802.enable(True)
nau7802.channel = 1
nau7802.gain = 1  # Gain of 1 for full-range single-ended signals


def read_len(samples=1):
    """Read and average multiple raw samples."""
    #for _ in range(samples):
    while not nau7802.available():
        pass
    voltage_uv = (nau7802.read() / 16777215) * 3300000
    linpot_travel_um = (voltage_uv - 7230) / -96.1
    linpot_travel_mm = (linpot_travel_um) / 1000
    return linpot_travel_mm


# --- Calibrate ---
print("NAU7802 Single-Ended Reader")
print("===========================\n")

print("Calibrating...")
#nau7802.calibrate("INTERNAL")
#nau7802.calibrate("OFFSET")
print("Done.\n")

# --- Main Loop ---
print("Reading A+ vs GND... (Ctrl+C to stop)\n")
try:
    while True:
        len = read_len(samples=1)
        print(f"Len(mm): {len:>10.4f}")
except KeyboardInterrupt:
    print("\nDone.")
