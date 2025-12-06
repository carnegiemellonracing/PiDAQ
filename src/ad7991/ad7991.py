from adafruit_bus_device.i2c_device import I2CDevice
import busio
import board
import time

class AD7991:    
    def __init__(self, i2c_handle, i2c_address=0x28, num_channels=4):
        assert (num_channels > 0 and num_channels <= 4)

        self.device = I2CDevice(i2c_handle, i2c_address)
        self.num_channels = num_channels
        
        # AD7991 Configuration Byte
        # Bit 7: 0 (reserved)
        # Bit 6-4: Channel selection (set bits for channels to convert)
        # Bit 3: REF_SEL (0 = use Vdd as reference, 1 = use external reference)
        # Bit 2: FLTR (0 = filter disabled, 1 = filter enabled)
        # Bit 1-0: Reserved
        
        # Enable channels 0 through (num_channels-1)
        # O(1) - Single configuration write
        channel_mask = 0
        for i in range(num_channels):
            channel_mask |= (1 << (7 - i))  # Channels are bits 7,6,5,4 for CH0-CH3
        
        configuration_byte = (
            channel_mask +      # Enable selected channels
            (0b0 << 3) +        # Use Vdd as reference (external ref available on pin 4)
            (0b0 << 2)          # Filter disabled for faster conversion
        )

        # Write configuration to AD7991
        # O(1) - Single I2C transaction
        with self.device:
            self.device.write(bytes([configuration_byte]))
    

    def read_adc(self):
        result = bytearray(self.num_channels * 2)

        with self.device:
            self.device.readinto(result)
        
        # Parse the 12-bit values from 2-byte pairs
        # O(n) where n = num_channels
        data = [0] * self.num_channels
        for i in range(self.num_channels):
            # Extract 12-bit value from bytes
            # Bits [13:12] contain channel ID, bits [11:0] contain data
            high_byte = result[2 * i]
            low_byte = result[2 * i + 1]
            
            # Combine bytes: keep lower 4 bits of high byte and all of low byte
            data[i] = ((high_byte & 0x0F) << 8) | low_byte
        
        return data


if __name__ == "__main__":
    i2c = busio.I2C(board.SCL, board.SDA)
    
    ad7991 = AD7991(i2c, i2c_address=0x28, num_channels=4)

    print("AD7991 Test - Reading 4 channels:")
    while True:
        values = ad7991.read_adc()
        print(f"CH0: {values[0]:4d}  CH1: {values[1]:4d}  CH2: {values[2]:4d}  CH3: {values[3]:4d}")
        time.sleep(0.1)

