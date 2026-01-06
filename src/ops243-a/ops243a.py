# OPS243-A Doppler Radar Sensor
# Library: https://github.com/graeb/OmnipresenseRadar
#
# Installation:
#   git clone https://github.com/graeb/OmnipresenseRadar.git
#   cd OmnipresenseRadar
#   pip install -e .
#
# Usage:
#   from ops243a.ops243a import OPS243A
#   sensor = OPS243A('/dev/ttyAMA0')
#   speed = sensor.read_speed()


class OPS243A:
    def __init__(self, uart_serial):
        self.port = uart_serial
        #GPIO.cleanup() #resets everything
        #GPIO.setmode(GPIO.BCM)
        #GPIO.setup(26, GPIO.OUT)

        #GPIO.output(26, GPIO.HIGH)
        #time.sleep(1)
        #GPIO.output(26, GPIO.LOW)
        #time.sleep(1)
        #GPIO.output(26, GPIO.HIGH)

    def read_dopplers(self):
        data = self.port.read(8)
        return data


if __name__ == "__main__":
    import time
    # from OmniPreSense import OPS243
    import serial 
    import RPi.GPIO as GPIO
    
    uart0_serial = serial.Serial(port="/dev/serial0", baudrate=19200, timeout=3.0)
    sensor = OPS243A(uart0_serial)
    
    buffer = b''

    while True:
        speed = sensor.read_dopplers()
        buffer += speed
        if b'\r\n' in buffer:
            line, buffer = buffer.split(b'\r\n', 1)
            value = float(line.decode('utf-8'))
            print("Speed:", value, "m/s")
        time.sleep(0.1)

