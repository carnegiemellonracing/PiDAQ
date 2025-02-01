# computes the average temperature from an MLX90640 data frame
def compute_average_temp(data_frame: list) -> int:
    data_frame = [float(temp) for temp in data_frame]
    if len(data_frame) != 768:
        raise Exception("Data frame must contain exactly 768 temperature values.")

    return int((sum(data_frame) / len(data_frame)))

# takes a given integer and splits its value into 4 seperate byte frames in a returned list
def split_integer_to_bytes(value: int) -> list[int]:
    if not (0 <= value <= 0xFFFFFFFF):
        raise Exception("The input integer must be between 0 and 0xFFFFFFFF (inclusive).")

    return [
        (value >> 24) & 0xFF,  # Extract the most significant byte
        (value >> 16) & 0xFF,  # Extract the second byte
        (value >> 8) & 0xFF,   # Extract the third byte
        value & 0xFF           # Extract the least significant byte
    ]

# returns a string of the given length by either padding it with spaces or splicing it
def limit_string_length(string: str, length: int) -> str:
    return str(string).ljust(length)[:length]