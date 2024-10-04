from adafruit_bus_device.i2c_device import I2CDevice
import busio
import board

# MAX11617 device I2C address (binary: 0110101, decimal: 53)
MAX11617_I2C_ADDRESS = 0x35


def init_max11617(i2c):
    # Open I2C connection with the MAX11617
    device = I2CDevice(i2c, MAX11617_I2C_ADDRESS)
    return device


# Configuration Byte
# REG = 0 (Configuration byte), SCAN1 = 1, SCAN0 = 1, CS3 = 0, CS2 = 1, CS1 = 0, CS0 = 1 (Channel 5), SGL/DIF = 1 (Single-ended mode)
configuration_byte = 0b01101001

def convert_to_length(raw_value):
    return 215-(raw_value*75/4060)

# Function to read from ADC
def read_adc(device):
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

    return convert_to_length(raw_value)


def main():
    i2c = busio.I2C(board.D1, board.D0)
    adc = init_max11617(i2c)
    # Read from the ADC and print the result in decimal
    adc_value = read_adc(adc)
    print(f"ADC Reading (Channel 5): {adc_value}")


if __name__ == "__main__":
    main()
