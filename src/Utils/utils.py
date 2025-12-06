#Utility functions for data conversion and test ID management


def uint16_to_bytes(value):
    return [value & 0xFF, value >> 8]


def bytes_to_uint16(byte_array):
    return byte_array[0] + (byte_array[1] << 8)


def test_id_is_active(test_id):
    return test_id >= 2 ** 15


def extract_test_id(test_id):
    return test_id & 0x7FFF

