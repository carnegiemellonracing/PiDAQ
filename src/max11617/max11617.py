from adafruit_bus_device.i2c_device import I2CDevice
import busio
import board
import time

#THIS IS NOW FOR THE AD7991 ADC
#Just not renaimed yet
class MAX11617:
    def __init__(self, i2c_handle, i2c_address, num_channels):
        assert (num_channels > 0)

        self.device = I2CDevice(i2c_handle, i2c_address)
        self.num_channels = num_channels

        #NO LONGER NEED SETUP BYTE. PENDING REMOVAL...
        #-----------------------------------------------------------#
        # setup_byte = (
        #     (0b1                << 7) +  # Setup byte
        #     (0b010              << 4) +  # Use external reference
        #     (0b0                << 3) +  # Internal clock
        #     (0b0                << 2) +  # Unipolar mode
        #     (0b1                << 1)    # No reset
        # )
        #-----------------------------------------------------------#
        
        # Creates channel enable mask based on num_channels
        #--------------------------------------------------------------#
        # For num_channels=4: enable CH0-CH3 (bits 7-4 = 1111 = 0xF0)
        # For num_channels=2: enable CH0-CH1 (bits 5-4 = 0011 = 0x30)
        channel_mask = (2 ** num_channels - 1) << (8 - num_channels)
        #--------------------------------------------------------------#
        

        # AD7991 Configuration Byte Format (8 bits):
        #----------------------------------------------------------------#
        # Bits 7-4: Channel selection (1 = enable channel for conversion)
        #   Bit 7: Enable CH3 
        #   Bit 6: Enable CH2
        #   Bit 5: Enable CH1
        #   Bit 4: Enable CH0
        # Bits 3-0: Reference selection and filter bits
        configuration_byte = (
            channel_mask +    # Bits 7-4: Enable channels 0 to (num_channels-1)
            (0b0 << 3) +      # Bit 3: 0 = External reference (using VIN3/VREF)
            (0b0 << 2) +      # Bit 2: 0 = Filter off
            (0b00 << 0)       # Bits 1-0: Standard operation

            #OUTDATED. PENDING REMOVAL...
            #-----------------------------------------------------------#
            #(0b0                << 7) +  # Configuration byte
            #(0b00               << 5) +  # Scanning mode: normal
            #((num_channels - 1) << 1) +  # Scan through to num_channels
            #(0b1                << 0)    # Single-ended mode
            #-----------------------------------------------------------#
        )
        #----------------------------------------------------------------#

        with self.device:

            #NO LONGER NEEDED. PENDING REMOVAL...
            #--------------------------------------#
            #self.device.write(bytes([setup_byte]))
            #--------------------------------------#

            self.device.write(bytes([configuration_byte]))
    

    def read_adc(self):
        result = bytearray(self.num_channels * 2) # <----- Read 2 bytes per channel (status byte + data byte for each)

        with self.device:
            self.device.readinto(result)
        
        #OUTDATED AND REPLACED. PENDING REMOVAL...
        #----------------------------------------------------------------#
        # for i in range(self.num_channels):
        #     data[i] = ((result[2 * i] & 0x0F) << 8) | result[2 * i + 1]
        #----------------------------------------------------------------#


        # Parsing of the ADC data
        #-------------------------------------------------------------------------#
        # Each channel returns 2 bytes:
        # Byte 1 (MSB): bits 7-4 = status (00 + channel ID), bits 3-0 = data[11:8]
        # Byte 2 (LSB): bits 7-0 = data[7:0]
        data = [0] * self.num_channels

        for i in range(self.num_channels):
            msb = result[2 * i]
            lsb = result[2 * i + 1]
            # Extract 12-bit ADC value
            data[i] = ((msb & 0x0F) << 8) | lsb
        #-------------------------------------------------------------------------#

        return data


if __name__ == "__main__":
    i2c = busio.I2C(board.SCL, board.SDA)
    
    #OUTDATED. PENDING REMOVAL...
    #--------------------------------#
    #max11617 = MAX11617(i2c, 0x35, 3)
    #--------------------------------#

    max11617 = MAX11617(i2c, 0x28, 4)

    while True:
        print(max11617.read_adc())
        time.sleep(1)
