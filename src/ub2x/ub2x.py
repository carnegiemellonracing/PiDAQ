# import serial
# #TODO: sudo apt-get install python-serial


# class UB2X:
#     def __init__(self, uart_serial):
#         self.port = uart_serial

#     def read_rideheight(self):
#         data = self.port.read(12) #read 12 bytes
#         return data

# if __name__ == "__main__":
#     import time
#     import serial 
    
#     uart0_serial = serial.Serial(port="/dev/serial0", baudrate=19200, timeout=3.0)
#     sensor = UB2X(uart0_serial)

#     while True:
#         height = sensor.read_rideheight()
#         time.sleep(0.1)



import serial
import struct
import time
# TODO: sudo apt-get install python-serial

class UB2X:
    def __init__(self, uart_serial):
        self.port = uart_serial

        # Read Measure Result command (Table 6-13)
        # AA 80 00 22 A2
        self.read_cmd = bytes([
            0xAA,  # Head
            0x80,  # Read + slave addr 0x00
            0x00,  # Register high
            0x22,  # Register low
            0xA2   # Checksum (from datasheet)
        ])
        self.turnlaseron = bytearray([
            0xAA,
            0x00,
            0x01,
            0xBE,
            0x00,
            0x01,
            0x00,
            0x01
        ])
        self.turnlaseron.append(sum(self.turnlaseron) & 0xFF)

        self.port.write(self.turnlaseron)



    def read_rideheight(self):
        # 1. Send read command
        self.port.write(self.read_cmd)

        # 2. Read reply (13 bytes total)
        reply = self.port.read(13)
        print(reply)

        #if len(reply) != 13:
        #    raise IOError(f"Incomplete reply: {len(reply)} bytes")

        # 3. Basic frame check
        if reply[0] != 0xAA:
            raise ValueError("Invalid frame header")

        # 4. Extract distance (bytes 6–9)
        # Payload Distance = 4 bytes, big-endian
        distance_raw = reply[6:10]
        distance = struct.unpack(">I", distance_raw)[0]

        # 5. Extract signal quality (bytes 10–11)
        sq = struct.unpack(">H", reply[10:12])[0]

        return distance, sq


if __name__ == "__main__":
    uart0_serial = serial.Serial(
        port="/dev/serial0",
        baudrate=19200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=3.0
    )

    sensor = UB2X(uart0_serial)

    while True:
        try:
            distance, sq = sensor.read_rideheight()
            print(f"Distance: {distance}, SQ: {sq}")
        except Exception as e:
            print("Error:", e)

        time.sleep(0.1)
