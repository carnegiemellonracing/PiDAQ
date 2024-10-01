import adafruit_mlx90640
import mlx.mlx90640 as mlx_lib
import time
import board
import busio
import numpy as np

NUM_ROWS = 24
NUM_COLUMNS = 32

# Initialize list to store timestamps for frame rate calculations
timestamps = []

def init_mlx90640():
    try:
        mlx = mlx_lib.Mlx9064x('I2C-1', i2c_addr=0x33, frame_rate=32.0)
        mlx.init()
        print("MLX addr detected on I2C")
        return mlx
    except Exception as e:
        print(f"Error initializing MLX90640: {e}")
        return None

def read_frame(mlx):
    try:
        raw_frame = mlx.read_frame()
        frame = mlx.do_compensation(raw_frame)

        # Display frame temperatures (optional)
        '''
        for h in range(NUM_ROWS):
            for w in range(NUM_COLUMNS):
                t = frame[h * NUM_COLUMNS + w]
                print("%0.1f, " % t, end="")
            print()
        print()
        '''

        return frame
    except Exception as e:
        print(f"Error reading frame: {e}")
        return None

def calculate_frame_rate(timestamps):
    # Calculate differences between consecutive timestamps
    time_diffs = np.diff(timestamps)

    if len(time_diffs) > 0:
        # Calculate frame rates (inverse of time differences)
        frame_rates = 1 / time_diffs

        # Calculate average, max, and min frame rates
        avg_frame_rate = np.mean(frame_rates)
        max_frame_rate = np.max(frame_rates)
        min_frame_rate = np.min(frame_rates)

        return avg_frame_rate, max_frame_rate, min_frame_rate
    else:
        return None, None, None

def main():
    mlx = init_mlx90640()

    if not mlx:
        print("Failed to initialize MLX90640. Exiting...")
        return

    try:
        while True:
            start_time = time.time()

            frame = read_frame(mlx)
            if frame is None:
                print("Error reading frame, skipping frame.")
                continue

            # Store timestamp for frame rate calculation
            timestamps.append(time.time())

            # Keep a maximum number of 100 timestamps to avoid memory issues
            if len(timestamps) > 100:
                timestamps.pop(0)

            # Calculate and display frame rate statistics every 10 frames
            if len(timestamps) > 10:
                avg_frame_rate, max_frame_rate, min_frame_rate = calculate_frame_rate(timestamps)

                if avg_frame_rate is not None:
                    print(f"Average Frame Rate: {avg_frame_rate:.2f} FPS")
                    print(f"Max Frame Rate: {max_frame_rate:.2f} FPS")
                    print(f"Min Frame Rate: {min_frame_rate:.2f} FPS")

            # Adjust sleep time to maintain constant frame rate
            time.sleep(max(0, (1 / 32.0) - (time.time() - start_time)))

    except KeyboardInterrupt:
        print("Program interrupted by user. Exiting...")

if __name__ == "__main__":
    main()

