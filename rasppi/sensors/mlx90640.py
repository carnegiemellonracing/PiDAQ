import time
import board
import busio
import adafruit_mlx90640

NUM_ROWS = 24
NUM_COLUMNS = 32


def init_mlx90640(i2c):
    mlx = adafruit_mlx90640.MLX90640(i2c)
    print("MLX addr detected on I2C", [hex(i) for i in mlx.serial_number])
    # if using higher refresh rates yields a 'too many retries' exception,
    # try decreasing this value to work with certain pi/camera combinations
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
    return mlx


def read_frame(mlx):
    frame = [0] * (NUM_ROWS * NUM_COLUMNS)
    try:
        mlx.getFrame(frame)
    except ValueError:
        # these happen, no biggie - retry
        return False

    for h in range(NUM_ROWS):
        for w in range(NUM_COLUMNS):
            t = frame[h * NUM_COLUMNS + w]
            print("%0.1f, " % t, end="")
        print()
    print()
    return frame


def main():
    while True:
        frame = read_frame()
        print(frame)


if __name__ == "__main__":
    main()
