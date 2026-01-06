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
    
    def read_dopplers(self):
        data = self.port.read(8)


if __name__ == "__main__":
    import time
    # from OmniPreSense import OPS243
    import serial 
    
    uart0_serial = serial.Serial(port="/dev/serial0", baudrate=19200, timeout=3.0)
    sensor = OPS243A(uart0_serial)
    
    while True:
        speed = sensor.read_dopplers()
        print(f"Speed: {speed:.2f} m/s")
        time.sleep(0.1)

