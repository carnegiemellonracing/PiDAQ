import spidev  # type: ignore
import RPi.GPIO as GPIO  # type: ignore
import time
from threading import Thread
# pylint: enable=import-error

GPIO.setwarnings(False)  # Disable GPIO warnings

# MCP2515 Registers and Commands
MCP2515_RESET = 0xC0
MCP2515_READ = 0x03
MCP2515_WRITE = 0x02
MCP2515_BIT_MODIFY = 0x05
MCP2515_READ_STATUS = 0xA0

# MCP2515 CANCTRL Register Values
MODE_NORMAL = 0x00
MODE_LOOPBACK = 0x40
MODE_CONFIG = 0x80

class MCP2515:
       
    def __init__(self, spi_handle, cs_pin=5, retries=3, timeout=1.0):
        self.spi = spi_handle
        self.cs_pin = cs_pin
        self.retries = retries
        self.timeout = timeout

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(cs_pin, GPIO.OUT)
        GPIO.output(cs_pin, GPIO.HIGH)
        self.reset()
        self.configure_baud_rate()
        
        self.FILTER_MAP = {
            0: 0x0,
            1: 0x4,
            2: 0x8,
            3: 0x10,
            4: 0x14,
            5: 0x18
        }
        
        self.MASK_MAP = {
            0: 0x20, 
            1: 0x24
        }
        
        self.CTRL_MAP = {
            0: 0x60,
            1: 0x70
        }

    def configure_baud_rate(self):
        # Set the baud rate to 250000 in configuration registers
        self.write_register(0x2A, 0x00)
        self.write_register(0x29, 0xB1)
        self.write_register(0x28, 0x05)

    def retry_operation(self, operation, *args, **kwargs):
        last_exception = None
        start_time = time.time()
        for _ in range(self.retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:  # pylint: disable=broad-exception-caught
                last_exception = e
                if time.time() - start_time > self.timeout:
                    break
                time.sleep(0.1)  # Small delay before retrying
        raise RuntimeError(f"""Operation failed after {
                           self.retries} retries: {last_exception}""")

    def reset(self):
        def _reset():
            GPIO.output(self.cs_pin, GPIO.LOW)
            self.spi.xfer([MCP2515_RESET])
            GPIO.output(self.cs_pin, GPIO.HIGH)
            time.sleep(0.1)  # Wait for the reset to complete

        self.retry_operation(_reset)

    def read_register(self, address):
        def _read_register(address):
            GPIO.output(self.cs_pin, GPIO.LOW)
            self.spi.xfer([MCP2515_READ, address])
            result = self.spi.xfer([0x00])[0]
            GPIO.output(self.cs_pin, GPIO.HIGH)
            return result

        return self.retry_operation(_read_register, address)

    def write_register(self, address, value):
        def _write_register(address, value):
            GPIO.output(self.cs_pin, GPIO.LOW)
            self.spi.xfer([MCP2515_WRITE, address, value])
            GPIO.output(self.cs_pin, GPIO.HIGH)

        self.retry_operation(_write_register, address, value)

    def bit_modify(self, address, mask, value):
        def _bit_modify(address, mask, value):
            GPIO.output(self.cs_pin, GPIO.LOW)
            self.spi.xfer([MCP2515_BIT_MODIFY, address, mask, value])
            GPIO.output(self.cs_pin, GPIO.HIGH)

        self.retry_operation(_bit_modify, address, mask, value)

    def set_mode(self, mode):
        def _set_mode(mode):
            self.write_register(0x0F, mode)
            # Verify the mode was set correctly
            current_mode = self.read_register(0x0F) & 0xE0
            if current_mode != mode:
                raise RuntimeError(
                    f"Failed to set MCP2515 mode to {hex(mode)}")

        self.retry_operation(_set_mode, mode)

    def set_normal_mode(self):
        self.set_mode(MODE_NORMAL)

    def set_loopback_mode(self):
        self.set_mode(MODE_LOOPBACK)
        
    def set_config_mode(self):
        self.set_mode(MODE_CONFIG)

    def read_status(self):
        def _read_status():
            GPIO.output(self.cs_pin, GPIO.LOW)
            status = self.spi.xfer([MCP2515_READ_STATUS, 0x00])[1]
            GPIO.output(self.cs_pin, GPIO.HIGH)
            return status

        return self.retry_operation(_read_status)

    def send_message(self, can_id, data, timeout=0.2):
        if not 0 <= can_id <= 0x7FF:
            raise ValueError("CAN ID must be 11 bits (0x000 to 0x7FF)")
        if len(data) > 8:
            raise ValueError("CAN data length must be 8 bytes or less")

        def _send_message(can_id, data):
            # Load TX buffer with CAN ID (11 bits)
            sid_high = (can_id >> 3) & 0xFF  # Higher 8 bits of CAN ID
            sid_low = (can_id << 5) & 0xE0   # Lower 3 bits of CAN ID

            # Set the standard identifier (SID) registers
            self.write_register(0x31, sid_high)  # TXB0SIDH
            self.write_register(0x32, sid_low)   # TXB0SIDL

            # Set the Data Length Code (DLC)
            dlc = len(data)
            self.write_register(0x35, dlc)  # TXB0DLC

            # Load data into the TX buffer
            for i, value in enumerate(data):
                self.write_register(0x36 + i, value)

            # Request to send
            # Set TXREQ to start transmission
            self.bit_modify(0x30, 0x08, 0x08)

        self.retry_operation(_send_message, can_id, data)

        # Wait for transmission to complete
        start_time = time.time()
        while self.read_register(0x30) & 0x08:  # TXB0CTRL - TXREQ bit
            if time.time() - start_time > timeout:
                # Abort the transmission if it's taking too long
                # ABAT bit in CANCTRL register
                self.bit_modify(0x0F, 0x10, 0x10)
                return False    
            time.sleep(0.01)  # Small delay to prevent busy-waiting

        # Clear TX interrupt flag
        self.bit_modify(0x2C, 0x1C, 0x00)  # Clear TXnIF flags
        return True

    def read_message(self):
        status = self.read_status()
        if status & 0x01:  # Check if RX0IF is set
            try:
                id_high = self.read_register(0x61)
                id_low = self.read_register(0x62)
                length = self.read_register(0x65) & 0x0F
                data = []
                for i in range(length):
                    data.append(self.read_register(0x66 + i))
                self.bit_modify(0x2C, 0x01, 0x00)  # Clear RX0IF
                return (id_high << 3) | (id_low >> 5), data, length
            except Exception as e:
                raise RuntimeError(
                    f"Failed to read CAN message: {e}") from e
        return None, None, None
    
    def set_acceptance_filter(self, filter_id, filter_value):
        filter_high = self.FILTER_MAP[filter_id]
        filter_low = filter_high + 1
        
        self.write_register(filter_high, filter_value >> 3)
        self.write_register(filter_low, filter_value << 5)
        
    def set_acceptance_mask(self, mask_id, mask_value):
        mask_high = self.MASK_MAP[mask_id]
        mask_low = mask_high + 1
        
        self.write_register(mask_high, mask_value >> 3)
        self.write_register(mask_low, mask_value << 5)
        
    def enable_filters(self, buffer_id, enable):
        ctrl_register = self.CTRL_MAP[buffer_id]
        
        if enable:
            self.write_register(ctrl_register, 0x00)
        else:
            self.write_register(ctrl_register, 0x60)
            

    def shutdown(self):
        def _shutdown():
            # Set MCP2515 to configuration mode before shutdown
            self.set_mode(MODE_CONFIG)
            self.spi.close()  # Close SPI interface
            GPIO.cleanup(self.cs_pin)  # Cleanup GPIO
        self.retry_operation(_shutdown)


if __name__ == "__main__":
    WRITE_PERIOD = 0.050
    READ_PERIOD = 0.001

    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 100000

    mcp = MCP2515(spi, cs_pin=5)
    mcp.set_loopback_mode()

    def write_task():
        start_time = time.time()   
        data_val = 0 
        while True:
            current_time = time.time()
            if current_time - start_time > WRITE_PERIOD:
                data = [data_val] * 4
                mcp.send_message(can_id=0x100, data=data)
                data_val = (data_val + 1) % 256
                start_time = current_time
            else:
                time.sleep(0.001)

    def read_task():
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > READ_PERIOD:
                read_can_id, read_can_data, read_can_dlc = mcp.read_message()
                if read_can_id is not None:
                    print(read_can_id, read_can_data, read_can_dlc)

                start_time = current_time
            else:
                time.sleep(0.001)

    write_thread = Thread(target=write_task)
    read_thread = Thread(target=read_task)

    write_thread.start()
    read_thread.start()


