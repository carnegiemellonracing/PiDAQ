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

from OmniPreSense import OPS243


class OPS243A:
    
    def __init__(self, uart_port='/dev/ttyAMA0'):
        """Initialize sensor on specified UART port"""
        self.sensor = OPS243(port=uart_port)
    
    def read_speed(self):
        """
        Read speed from sensor
        Returns: Speed in m/s (float)
        """
        return self.sensor.getSpeed()
    
    def close(self):
        """Close the sensor connection"""
        self.sensor.close()


if __name__ == "__main__":
    import time
    
    # Test the sensor
    sensor = OPS243A('/dev/ttyAMA0')
    
    try:
        while True:
            speed = sensor.read_speed()
            print(f"Speed: {speed:.2f} m/s")
            time.sleep(0.1)
    except KeyboardInterrupt:
        sensor.close()
