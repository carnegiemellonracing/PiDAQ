from adafruit_bus_device.i2c_device import I2CDevice
import busio
import board
import time

class MAX11617:
    def __init__(self, i2c_handle, i2c_address, num_channels):
        assert (num_channels > 0)

        self.device = I2CDevice(i2c_handle, i2c_address)
        self.num_channels = num_channels

        setup_byte = (
            (0b1                << 7) +  # Setup byte
            (0b010              << 4) +  # Use external reference
            (0b0                << 3) +  # Internal clock
            (0b0                << 2) +  # Unipolar mode
            (0b1                << 1)    # No reset
        )

        configuration_byte = (
            (0b0                << 7) +  # Configuration byte
            (0b00               << 5) +  # Scanning mode: normal
            ((num_channels - 1) << 1) +  # Scan through to num_channels
            (0b1                << 0)    # Single-ended mode
        )

        with self.device:
            self.device.write(bytes([setup_byte]))
            self.device.write(bytes([configuration_byte]))
    

    def read(self):
        result = bytearray(self.num_channels * 2)

        with self.device:
            self.device.readinto(result)
        
        data = [0] * self.num_channels
        for i in range(self.num_channels):
            data[i] = ((result[2 * i] & 0x0F) << 8) | result[2 * i + 1]
        
        return data


if __name__ == "__main__":
    i2c = busio.I2C(board.SCL, board.SDA)
    max11617 = MAX11617(i2c, 0x35, 3)

    while True:
        print(max11617.read())
        time.sleep(1)
