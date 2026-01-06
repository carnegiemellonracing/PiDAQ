import serial
#TODO: sudo apt-get install python-serial


class UB2X:
    def __init__(self, uart_serial):
        self.serial = uart_serial

    def read_rideheight(self):
        data = self.serial.read(16) #reads 16 bytes