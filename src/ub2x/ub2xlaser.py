import serial
import struct
import time
import RPi.GPIO as GPIO


class UB2X:
    def __init__(self, uart_serial):
        self.port = uart_serial

        # GPIO.cleanup() #resets everything
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(26, GPIO.OUT)
        GPIO.output(26, GPIO.HIGH)

        time.sleep(0.1)
        GPIO.output(26, GPIO.LOW)


        self.set_auto_baud = bytes([0x55])
        self.port.write(self.set_auto_baud)
        # while True:
        #    self.port.write(0x55)
        #    print(self.port.read(9))
        # Read distance command (Table 6-13)
        self.read_cmd = bytes([
            0xAA, 0x80, 0x00, 0x22, 0xA2
        ])

        self.get_status = bytes([
            0xAA, 0x80, 0x00, 0x00, 0x80
        ])

        self.get_voltage = bytes([
            0xAA, 0x80, 0x00, 0x06, 0x86
        ])

        self.read_measure_result = bytes([
            0x00, 0x80, 0x00, 0x22, 0xA2
        ])
        self.continuous_auto = bytes([
            0xAA, 0x00, 0x00, 0x20, 0x00, 0x01, 0x00, 0x04, 0x25])
        print("hey get status")
        self.port.write(self.get_status)
        print(self.port.read(100))
        print("hey get voltage")
        self.port.write(self.get_voltage)
        print(self.port.read(100))
        print("hey get measure result")
        self.port.write(self.read_measure_result)
        print(self.port.read(100))
        self.port.write(self.continuous_auto)
        print("hey read continuous")
        print(self.port.read(100))

    

        # while (True):
        #     if self.port.in_waiting:
        #         data = self.port.read(self.port.in_waiting)
        #         print(data.hex())
    def _checksum(self, data):
        return sum(data) & 0xFF

    def read_rideheight(self):
        # Send read command
        self.port.write(self.read_cmd)

        # Read reply (13 bytes)
        reply = self.port.read(13)
        print(reply)
        # if len(reply) != 13:
        #     raise IOError("Incomplete read reply")

        #if reply[0] != 0xAA:
        #    raise ValueError("Invalid header")

        # Distance bytes 6–9 (big-endian)
        #distance = struct.unpack(">I", reply[6:10])[0]

        # Signal quality bytes 10–11
        #sq = struct.unpack(">H", reply[10:12])[0]

        distance = 'ok'
        sq = 'ok'

        return distance, sq

    def set_laser(self, enable: bool):
        zz = 0x01 if enable else 0x00

        frame = bytearray([
            0xAA,       # Head
            0x00,       # Write + slave 0x00
            0x01,       # Register high
            0xBE,       # Register low
            0x00,       # Payload count high
            0x01,       # Payload count low
            0x00,       # Reserved
            zz          # Laser on/off
        ])

        frame.append(self._checksum(frame))

        self.port.write(frame)

        # Read reply (9 bytes)
        reply = self.port.read(9)
        #if len(reply) != 9:
        #    raise IOError("No laser ACK")

        return reply


if __name__ == "__main__":
    uart0_serial = serial.Serial(
        port="/dev/serial0",
        baudrate=115200,
        timeout=3.0
    )

    sensor = UB2X(uart0_serial)

    # Turn laser ON
    sensor.set_laser(True)
    time.sleep(0.2)

    while True:
        distance, sq = sensor.read_rideheight()
        print(f"Distance: {distance}, SQ: {sq}")
        time.sleep(0.1)

    # Turn laser OFF (if needed)
    # sensor.set_laser(False)

