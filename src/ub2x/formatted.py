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
        self.set_auto_baud = bytes([0x55])
        self.port.write(self.set_auto_baud)
        time.sleep(0.1)
        # Drain auto-baud reply (1 byte address)
        if self.port.in_waiting:
            self.port.read(self.port.in_waiting)

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
            0xAA, 0x80, 0x00, 0x22, 0xA2
        ])
        self.continuous_auto = bytes([
            0xAA, 0x00, 0x00, 0x20, 0x00, 0x01, 0x00, 0x04, 0x25
        ])

        # Read status
        self.port.write(self.get_status)
        reply = self.port.read(9)
        if len(reply) >= 8:
            status_code = struct.unpack(">H", reply[6:8])[0]
            print(f"Status: 0x{status_code:04X}")
        else:
            print(f"Status: incomplete reply ({reply.hex()})")

        # Read voltage
        self.port.write(self.get_voltage)
        reply = self.port.read(9)
        if len(reply) >= 8:
            voltage_bcd = reply[6:8].hex()
            print(f"Input Voltage: {voltage_bcd} mV")
        else:
            print(f"Voltage: incomplete reply ({reply.hex()})")

        # Read cached measure result
        #self.port.write(self.read_measure_result)
        #reply = self.port.read(13)
        #if len(reply) >= 12:
        #    distance_mm = struct.unpack(">I", reply[6:10])[0]
        #    sq = struct.unpack(">H", reply[10:12])[0]
        #    print(f"Cached Distance: {distance_mm} mm ({distance_mm / 1000:.3f} m), SQ: {sq}")
        #else:
        #    print(f"Measure result: incomplete reply ({reply.hex()})")

        # Start continuous auto measure
        self.port.write(self.continuous_auto)
        print("Continuous auto measure started")
        while True:
            reply = self.port.read(13)
            if len(reply) >= 12:
                distance_mm = struct.unpack(">I", reply[6:10])[0]
                sq = struct.unpack(">H", reply[10:12])[0]
                print(f"Cached Distance: {distance_mm} mm ({distance_mm / 1000:.3f} m), SQ: {sq}")
            else:
                print(f"Measure result: incomplete reply ({reply.hex()})")
            

    def _checksum(self, data):
        return sum(data) & 0xFF

    def read_rideheight(self):
        self.port.write(self.read_cmd)
        reply = self.port.read(13)
        if len(reply) < 12:
            return None, None
        if reply[0] == 0xEE:
            err_code = struct.unpack(">H", reply[6:8])[0]
            print(f"Error: 0x{err_code:04X}")
            return None, None
        distance_mm = struct.unpack(">I", reply[6:10])[0]
        sq = struct.unpack(">H", reply[10:12])[0]
        return distance_mm, sq

    def set_laser(self, enable: bool):
        zz = 0x01 if enable else 0x00
        frame = bytearray([
            0xAA, 0x00, 0x01, 0xBE, 0x00, 0x01, 0x00, zz
        ])
        frame.append(self._checksum(frame[1:]))
        self.port.write(frame)
        reply = self.port.read(9)
        return reply


if __name__ == "__main__":
    uart0_serial = serial.Serial(
        port="/dev/serial0",
        baudrate=115200,
        timeout=3.0
    )
    sensor = UB2X(uart0_serial)
    # sensor.set_laser(True)
    time.sleep(0.2)

    #while True:
    #    distance_mm, sq = sensor.read_rideheight()
   #     if distance_mm is not None:
    #        print(f"Distance: {distance_mm} mm ({distance_mm / 1000:.3f} m), SQ: {sq}")
     #   else:
      #      print("No valid reading")
       # time.sleep(0.1)
