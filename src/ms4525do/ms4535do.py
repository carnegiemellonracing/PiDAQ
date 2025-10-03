# import smbus
# import time

# I2C_BUS = 1
# ADDR = 0x28  # Example address; verify with i2cdetect

# bus = smbus.SMBus(I2C_BUS)

# def read_raw():
#     # some modules require writing a “start convert” / command; if so, send that here
#     # e.g., bus.write_byte(ADDR, <command_byte>)
#     # wait for conversion time (datasheet gives max conversion delay)
#     time.sleep(0.01)  # example 10 ms delay, adjust as needed

#     # now read data (e.g. 4 bytes, or 5 bytes; check your variant in datasheet)
#     # Here, assume reading 4 bytes starting at register 0
#     data = bus.read_i2c_block_data(ADDR, 0, 4)
#     # Combine into a 16-bit or 14-bit raw value
#     raw = (data[0] << 8) | data[1]
#     return raw

# def convert_pressure(raw_counts):
#     # Use datasheet constants; this is an example form
#     # Suppose Pmin = 0 psi, Pmax = 1 psi, offset = 0.1 * fullscale, span = 0.8 * fullscale
#     # fullscale = 2^14 − 1 = 16383
#     fullscale = 16383
#     offset = 0.1 * fullscale
#     span = 0.8 * fullscale
#     Pmin = 0.0  # psi
#     Pmax = 1.0  # psi
#     pressure = ((raw_counts - offset) * (Pmax - Pmin) / span) + Pmin
#     return pressure

# if __name__ == "__main__":
#     while True:
#         r = read_raw()
#         p = convert_pressure(r)
#         print(f"Raw: {r}, Pressure: {p:.4f} psi")
#         time.sleep(1.0)


import smbus
import time

# ----------------- I2C setup -----------------
I2C_BUS = 1
ADDR    = 0x28    # Confirm with:  i2cdetect -y 1
bus = smbus.SMBus(I2C_BUS)

# ------------- MS4525DO transfer setup -------------
# Set TYPE_A=True for sensors with 10–90% output span
# Set TYPE_A=False for sensors with 5–95% output span
TYPE_A = True
if TYPE_A:
    C_MIN, C_MAX = 1638.3, 14745.3   # 10–90% of 2^14-1
else:
    C_MIN, C_MAX = 819.0, 15563.0    # 5–95% of 2^14-1

# Sensor pressure range (adjust to match your part)
PMIN_PSI, PMAX_PSI = 0.0, 1.0        # e.g., ±1 psi or 0–1 psi variant

# Optional zeroing at startup: average N samples and subtract as offset
ZERO_SAMPLES = 50

# Global offset (in psi) applied inside convert_pressure()
_offset_psi = 0.0


def read_raw():
    """
    Read one MS4525DO frame and return *pressure counts* (14-bit).
    Keeps your original function signature: returns a single integer.

    Raises IOError if the sensor reports a diagnostic/fault (status=3).
    """
    # Read 4 bytes: [status+P13..P8, P7..P0, T10..T3, T2..T0+pad]
    b = bus.read_i2c_block_data(ADDR, 0x00, 4)

    status = (b[0] >> 6) & 0x03
    if status == 3:
        # Diagnostic/fault condition; upstream code can catch this
        raise IOError("MS4525DO diagnostic/fault")

    # 14-bit pressure counts
    p_counts = ((b[0] & 0x3F) << 8) | b[1]
    return p_counts


def convert_pressure(raw_counts):
    """
    Convert 14-bit pressure counts -> pressure in psi using the proper
    linear map over the calibrated span, then subtract the startup offset.
    Keeps your original function signature: takes counts, returns psi.
    """
    # Linear map from counts over calibrated span to sensor's psi range
    p_psi = (raw_counts - C_MIN) * (PMAX_PSI - PMIN_PSI) / (C_MAX - C_MIN) + PMIN_PSI
    # Apply zero offset (computed at startup)
    return p_psi - _offset_psi


def _zero_offset():
    """Optional: compute average psi at rest and store as _offset_psi."""
    global _offset_psi
    if ZERO_SAMPLES <= 0:
        return
    acc = 0.0
    n = 0
    for _ in range(ZERO_SAMPLES):
        try:
            # Reuse the exact decoding path used by read_raw()/convert_pressure()
            b = bus.read_i2c_block_data(ADDR, 0x00, 4)
            status = (b[0] >> 6) & 0x03
            if status == 3:
                continue  # skip diagnostic frames
            p_counts = ((b[0] & 0x3F) << 8) | b[1]
            p_psi = (p_counts - C_MIN) * (PMAX_PSI - PMIN_PSI) / (C_MAX - C_MIN) + PMIN_PSI
            acc += p_psi
            n += 1
        except Exception:
            pass
        time.sleep(0.01)
    if n > 0:
        _offset_psi = acc / n


if __name__ == "__main__":
    # Optional: capture small static offset at startup
    _zero_offset()

    while True:
        try:
            r = read_raw()                       # 14-bit counts
            p = convert_pressure(r)              # psi
            print(f"Raw: {r}, Pressure: {p:.4f} psi")
        except IOError as e:
            # Sensor reported a diagnostic/fault; brief pause and retry
            print(f"Sensor fault: {e}")
            time.sleep(0.1)
            continue
        except Exception as e:
            # Any other I/O issue
            print(f"I2C error: {e}")
        time.sleep(1.0)
