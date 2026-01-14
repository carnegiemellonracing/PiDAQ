# UART Distance Sensor
# Based on 1-shot Auto Distance Measure protocol
#
# Usage:
#   from distance_sensor import DistanceSensor
#   sensor = DistanceSensor(uart_serial)
#   distance, quality = sensor.read_distance()
#

import time


class DistanceSensor:
    def __init__(self, uart_serial):
        self.port = uart_serial

    # ----------------------------
    # Checksum: 8-bit sum
    # ----------------------------
    def _checksum(self, data: bytes) -> int:
        return sum(data) & 0xFF

    # ----------------------------
    # Send 1-shot auto measure command
    # ----------------------------
    def _send_measure_cmd(self):
        frame = bytearray([
            0xAA,       # Head
            0x00,       # RW / Slave address
            0x00, 0x20, # Register 0x0020
            0x00, 0x01, # Payload count
            0x00,       # Payload
            0x00        # Reserved
        ])

        frame.append(self._checksum(frame))
        self.port.write(frame)

    # ----------------------------
    # Read distance result
    # ----------------------------
    def read_distance(self):
        """
        Returns:
            (distance_mm, signal_quality)
        """
        # Send command
        self._send_measure_cmd()

        # Small delay for measurement
        time.sleep(0.05)

        # Read fixed-length reply (13 bytes)
        data = self.port.read(13)

        if len(data) != 13:
            return None, None

        # Validate header
        if data[0] != 0xAA:
            return None, None

        # Validate checksum
        if self._checksum(data[:-1]) != data[-1]:
            return None, None

        # Validate register (0x0022)
        reg = (data[2] << 8) | data[3]
        if reg != 0x0022:
            return None, None

        # Distance (bytes 6..9)
        distance_mm = (
            (data[6] << 24) |
            (data[7] << 16) |
            (data[8] << 8) |
            data[9]
        )

        # Signal Quality (bytes 10..11)
        signal_quality = (data[10] << 8) | data[11]

        return distance_mm, signal_quality

if __name__ == "__main__":
    import serial
    import time

    uart0_serial = serial.Serial(
        port="/dev/serial0",
        baudrate=115200,
        timeout=1.0
    )

    sensor = DistanceSensor(uart0_serial)

    while True:
        distance, quality = sensor.read_distance()

        if distance is not None:
            print(f"Distance: {distance} mm | Signal Quality: {quality}")
        else:
            print("No valid measurement")

        time.sleep(0.2)

