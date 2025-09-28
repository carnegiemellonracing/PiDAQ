import smbus
import time

I2C_BUS = 1
ADDR = 0x28  # Example address; verify with i2cdetect

bus = smbus.SMBus(I2C_BUS)

def read_raw():
    # some modules require writing a “start convert” / command; if so, send that here
    # e.g., bus.write_byte(ADDR, <command_byte>)
    # wait for conversion time (datasheet gives max conversion delay)
    time.sleep(0.01)  # example 10 ms delay, adjust as needed

    # now read data (e.g. 4 bytes, or 5 bytes; check your variant in datasheet)
    # Here, assume reading 4 bytes starting at register 0
    data = bus.read_i2c_block_data(ADDR, 0, 4)
    # Combine into a 16-bit or 14-bit raw value
    raw = (data[0] << 8) | data[1]
    return raw

def convert_pressure(raw_counts):
    # Use datasheet constants; this is an example form
    # Suppose Pmin = 0 psi, Pmax = 1 psi, offset = 0.1 * fullscale, span = 0.8 * fullscale
    # fullscale = 2^14 − 1 = 16383
    fullscale = 16383
    offset = 0.1 * fullscale
    span = 0.8 * fullscale
    Pmin = 0.0  # psi
    Pmax = 1.0  # psi
    pressure = ((raw_counts - offset) * (Pmax - Pmin) / span) + Pmin
    return pressure

if __name__ == "__main__":
    while True:
        r = read_raw()
        p = convert_pressure(r)
        print(f"Raw: {r}, Pressure: {p:.4f} psi")
        time.sleep(1.0)
