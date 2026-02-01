from adafruit_bus_device.i2c_device import I2CDevice
import busio
import board
import time

#TODO: rename to ADC new part num
class MAX11617:
    def __init__(self, i2c_handle, i2c_address, num_channels):
        assert (num_channels > 0)

        self.device = I2CDevice(i2c_handle, i2c_address)
        self.num_channels = num_channels

  
        configuration_byte = (
            (0b1111 << 4) + # Bits 7-4: Enable channels (1 if used)
            (0b0 << 3) + # Bit 3: 0 = using supply as Vref
            (0b1 << 2) + # Bit 2: 1 = Filter off -- may want to try with filter on
            (0b00) # Bits 1-0: 00 = bit trial and sample interval delay mechanism is implemented
        )

        with self.device:
            self.device.write(bytes([configuration_byte]))
    

    def read_adc(self):
        result = bytearray(self.num_channels * 2)

        with self.device:
            self.device.readinto(result)
      
        data = [0] * self.num_channels

        for channel in range(self.num_channels):
            data[channel] = ((result[2*channel] & 0x0F) << 8) | result[2*channel + 1]

        return data


if __name__ == "__main__":
    i2c = busio.I2C(board.SCL, board.SDA)
    max11617 = MAX11617(i2c, 0x35, 4)

    while True:
        print(max11617.read_adc())
        time.sleep(1)
