import serial

class JRT20Hz:
    def initialize(self):
        """
        The sensor requires an auto-baudrate stage. 
        Send 0x55 and the module will reply with its address (default 0x00)[cite: 30, 98].
        """
        self.port.write(b'\x55')
        reply = self.port.read(1)
        if reply:
            print(f"Sensor initialized. Module Address: {reply.hex()}")
            return True
        return False

    def read_distance(self):
        """
        Sends a 1-shot Auto Distance Measure command[cite: 62].
        Command: AA 00 00 20 00 01 00 00 21
        Returns: Distance in meters.
        """
        # Hex command for 1-shot Auto Distance Measure [cite: 62]
        cmd = b'\xAA\x00\x00\x20\x00\x01\x00\x00\x21'
        self.port.write(cmd)
    
        # The reply is 13 bytes long 
        # Format: Head(1) + Addr(1) + Reg(2) + Count(2) + Distance(4) + SQ(2) + Checksum(1)
        response = self.port.read(13)
    
        if len(response) == 13 and response[0] == 0xAA:
            # Distance is in bytes 6, 7, 8, 9 in millimeters 
            dist_mm = int.from_bytes(response[6:10], byteorder='big')
            return dist_mm / 1000.0  # Convert to meters
        elif len(response) > 0 and response[0] == 0xEE:
            print("Sensor Error Reported") [cite: 70]
            return None
        return None

    def start_continuous_ascii(self):
        """
        Starts 20Hz continuous measure with ASCII output (easier to read)[cite: 80].
        Command: AA 00 00 24 00 01 02 07 2F (approx based on protocol logic)
        """
        # Sending command for 20Hz ASCII output [cite: 79, 80]
        cmd = b'\xAA\x00\x00\x24\x00\x01\x02\x07\x2F'
        self.port.write(cmd)

    def stop_continuous(self):
        """
        Send 'X' (0x58) to stop continuous measurement[cite: 71, 84].
        """
        self.port.write(b'X')

# Default baudrate for this series is 115200 
uart0_serial = serial.Serial(port="/dev/serial0", baudrate=115200, timeout=1.0)
sensor = JRT20Hz(uart0_serial)

if sensor.initialize():
    print("Starting measurements...")
    try:
        while True:
            distance = sensor.read_distance()
            if distance is not None:
                print(f"Height/Distance: {distance:.3f} m")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopped by user")
