import serial
import struct
import time
import RPi.GPIO as GPIO


class UB2X:
    def __init__(self, uart_serial):
        self.port = uart_serial
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(26, GPIO.OUT)
        GPIO.output(26, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(26, GPIO.LOW)
        self.port.write(bytes([0x55]))
        time.sleep(0.1)
        # Drain auto-baud reply
        if self.port.in_waiting:
            self.port.read(self.port.in_waiting)

        # Read status
        self.port.write(bytes([0xAA, 0x80, 0x00, 0x00, 0x80]))
        reply = self.port.read(9)
        if len(reply) >= 8:
            status_code = struct.unpack(">H", reply[6:8])[0]
            print(f"Status: 0x{status_code:04X}")
        else:
            print(f"Status: incomplete reply ({reply.hex()})")

        # Read voltage
        self.port.write(bytes([0xAA, 0x80, 0x00, 0x06, 0x86]))
        reply = self.port.read(9)
        if len(reply) >= 8:
            voltage_bcd = reply[6:8].hex()
            print(f"Input Voltage: {voltage_bcd} mV")
        else:
            print(f"Voltage: incomplete reply ({reply.hex()})")

    def start_continuous(self):
        """Start continuous auto measure (up to 255 replies)."""
        self.port.write(bytes([
            0xAA, 0x00, 0x00, 0x20, 0x00, 0x01, 0x00, 0x04, 0x25
        ]))
        print("Continuous auto measure started")

    def start_continuous_slow(self):
        self.port.write(bytes([
            0xAA, 0x00, 0x00, 0x20, 0x00, 0x01, 0x00, 0x05, 0x26
        ]))
    def start_continuous_fast(self):
        """Start continuous fast measure."""
        self.port.write(bytes([
            0xAA, 0x00, 0x00, 0x20, 0x00, 0x01, 0x00, 0x06, 0x27
        ]))
        print("Continuous fast measure started")

    def start_continuous_20hz(self):
        """Start continuous 20Hz measure."""
        self.port.write(bytes([
            0xAA, 0x00, 0x00, 0x24, 0x00, 0x01, 0x00, 0x07, 0x2C
        ]))
        print("Continuous 20Hz measure started")

    def stop_continuous(self):
        """Stop continuous measure by sending 'X' (0x58)."""
        self.port.write(bytes([0x58]))
        time.sleep(0.05)
        if self.port.in_waiting:
            self.port.read(self.port.in_waiting)
        print("Continuous measure stopped")

    def read_continuous(self):
        """Read one frame from the continuous stream.
        Returns (distance_mm, sq) or (None, None) on error/timeout."""
        # Sync to frame header
        while True:
            byte = self.port.read(1)
            if len(byte) == 0:
                return None, None  # timeout
            if byte[0] == 0xAA:
                break
            if byte[0] == 0xEE:
                rest = self.port.read(8)
                if len(rest) >= 7:
                    err_code = struct.unpack(">H", rest[5:7])[0]
                    print(f"Error: 0x{err_code:04X}")
                return None, None

        # Read remaining 12 bytes (13 byte frame - 1 header)
        rest = self.port.read(12)
        if len(rest) < 11:
            return None, None

        # rest[5:9] = Distance (4 bytes BE), rest[9:11] = SQ (2 bytes BE)
        distance_mm = struct.unpack(">I", rest[5:9])[0]
        sq = struct.unpack(">H", rest[9:11])[0]
        return distance_mm, sq

    def set_laser(self, enable: bool):
        zz = 0x01 if enable else 0x00
        frame = bytearray([0xAA, 0x00, 0x01, 0xBE, 0x00, 0x01, 0x00, zz])
        frame.append(sum(frame[1:]) & 0xFF)
        self.port.write(frame)
        return self.port.read(9)


if __name__ == "__main__":
    uart0_serial = serial.Serial(
        port="/dev/serial0",
        baudrate=115200,
        timeout=3.0
    )
    sensor = UB2X(uart0_serial)
    #sensor.set_laser(True)
    time.sleep(0.2)

    sensor.start_continuous_slow()

    try:
        while True:
            distance_mm, sq = sensor.read_continuous()
            if distance_mm is not None:
                print(f"Distance: {distance_mm} mm ({distance_mm / 1000:.3f} m), SQ: {sq}")
            else:
                print("No valid reading")
    except KeyboardInterrupt:
        sensor.stop_continuous()
        sensor.set_laser(False)
        GPIO.cleanup()
        print("Shutdown complete")
