import serial
import time

# ----------------------------
# UART configuration
# ----------------------------
PORT = "/dev/ttyUSB0"     # Windows: "COM3"
BAUDRATE = 115200
TIMEOUT = 1.0             # seconds

# ----------------------------
# Helper: checksum (8-bit sum)
# ----------------------------
def calc_checksum(data: bytes) -> int:
    return sum(data) & 0xFF

# ----------------------------
# Build 1-shot auto measure command
# ----------------------------
def build_start_measure_cmd():
    frame = bytearray([
        0xAA,       # Head
        0x00,       # RW / Slave address
        0x00, 0x20, # Register address 0x0020
        0x00, 0x01, # Payload count = 1
        0x00,       # Payload (start measure)
        0x00        # Reserved / padding
    ])

    checksum = calc_checksum(frame)
    frame.append(checksum)
    return bytes(frame)

# ----------------------------
# Parse reply frame
# ----------------------------
def parse_reply(frame: bytes):
    if len(frame) < 13:
        raise ValueError("Frame too short")

    if frame[0] != 0xAA:
        raise ValueError("Invalid header")

    # Verify checksum
    if calc_checksum(frame[:-1]) != frame[-1]:
        raise ValueError("Checksum mismatch")

    reg = (frame[2] << 8) | frame[3]
    if reg != 0x0022:
        raise ValueError(f"Unexpected register: 0x{reg:04X}")

    payload_len = (frame[4] << 8) | frame[5]
    if payload_len != 3:
        raise ValueError("Unexpected payload length")

    # Distance: bytes 6..9
    distance = (
        (frame[6] << 24) |
        (frame[7] << 16) |
        (frame[8] << 8) |
        frame[9]
    )

    # Signal Quality: bytes 10..11
    signal_quality = (frame[10] << 8) | frame[11]

    return distance, signal_quality

# ----------------------------
# Main
# ----------------------------
def main():
    ser = serial.Serial(
        port=PORT,
        baudrate=BAUDRATE,
        timeout=TIMEOUT
    )

    time.sleep(0.2)  # allow UART to settle

    cmd = build_start_measure_cmd()
    print("TX:", cmd.hex(" "))

    ser.write(cmd)

    # Read reply (fixed 13 bytes according to protocol)
    reply = ser.read(13)
    print("RX:", reply.hex(" "))

    if not reply:
        print("No response")
        return

    distance, sq = parse_reply(reply)
    print(f"Distance: {distance} mm")
    print(f"Signal Quality: {sq}")

    ser.close()

if __name__ == "__main__":
    main()

