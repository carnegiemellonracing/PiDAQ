import time
import queue

mcp_queue = queue.Queue()
FILTER_ID = 0x69

# Set up filters
def setup_filter(mcp, filter_id):
	mcp.set_mode(MODE_CONFIG)
	mcp.write_register(0x60, 0x00)
	mcp.write_register(0x00, filter_id >> 3)
	mcp.write_register(0x01, filter_id << 5)
	mcp.write_register(0x20, 0xFF)
	mcp.write_register(0x21, 0xE0)
	mcp.set_normal_mode()

def send_data(data):
  mcp_queue.put(data)


# Main Thread Function
def run_mcp():
    # Initialize MCP2515 with default settings
    mcp = MCP2515(spi_channel=0, cs_pin=5)
    setup_filter(mcp, FILTER_ID)
    # Set to loopback mode
    mcp.set_loopback_mode()

    data = [0,0,0,0]
    print(data)
    while True:
        try:
            data = mcp_queue.get()
#            print(data)
            mcp.send_message(can_id=0x69, data=data)
            mcp_queue.task_done()

            # Read message
            can_id, data = mcp.read_message(timeout=1.0)

            if can_id is not None:
                print("Message from", hex(can_id))
                print("Message data:", data)
                message_str = "::".join([f"0x{i:02X}" for i in data])
                print(message_str)

        except Exception as e:
            print(e)
            print(data)
            print("MCP PROBLEM !!!!!!!!!!!!!!!!!")
            mcp.shutdown()

        time.sleep(0.05)