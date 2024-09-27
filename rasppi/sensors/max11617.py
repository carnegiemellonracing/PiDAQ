import board
import busio
from adafruit_bus_device.i2c_device import I2CDevice

# I2C setup
i2c = busio.I2C(board.SCL, board.SDA)

# MAX11617 device I2C address (binary: 0110101, decimal: 53)
MAX11617_I2C_ADDRESS = 0x35

# Open I2C connection with the MAX11617
device = I2CDevice(i2c, MAX11617_I2C_ADDRESS)

# Configuration Byte
# REG = 0 (Configuration byte), SCAN1 = 1, SCAN0 = 1, CS3 = 0, CS2 = 1, CS1 = 0, CS0 = 1 (Channel 5), SGL/DIF = 1 (Single-ended mode)
configuration_byte = 0b01101011

# Function to read from ADC
def read_adc():
    # Write the configuration byte to the device to select channel 5
    with device:
        device.write(bytes([configuration_byte]))

    # Prepare to read two bytes of data (the result)
    result = bytearray(2)
    with device:
        device.readinto(result)
    
    # Parse the result
    # The 12-bit result is encoded as follows:
    # First 4 bits of the first byte are padding, the next 8 bits are the most significant bits (MSBs)
    # The next 4 bits of the second byte are the least significant bits (LSBs)
    raw_value = ((result[0] & 0x0F) << 8) | result[1]
    
    # Return the 12-bit ADC value
    return raw_value

# Read from the ADC and print the result in decimal
adc_value = read_adc()
print(f"ADC Reading (Channel 5): {adc_value}")
