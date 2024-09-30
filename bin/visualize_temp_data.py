import time
import numpy as np
import matplotlib.pyplot as plt
import sys
import csv

fileName = sys.argv[1]

plt.ion()
fig, ax = plt.subplots(figsize=(12, 7))

# Set a constant scale (vmin, vmax) and use a blue-to-red gradient (coolwarm colormap)
diff_mode = False
speed_up_factor = 1
vmin = -30 if diff_mode else 25  # Set your desired minimum value for the color scale
vmax = 30 if diff_mode else 90  # Set your desired maximum value for the color scale
therm1 = ax.imshow(np.zeros((24, 32)), vmin=vmin, vmax=vmax, cmap='coolwarm')

cbar = fig.colorbar(therm1)
cbar.set_label('Temperature [$^{\circ}$C]', fontsize=14)

t_array = []
max_retries = 5

first_timestamp = None
last_timestamp = None
last_frame = np.zeros(24 * 32)

# Set a title for the plot
ax.set_title('Thermal Camera Data')

with open(fileName, 'r') as file:
    reader = csv.reader(file)
    header = next(reader)  # Skip the header row

    for row in reader:
        # Assuming the first column holds the timestamp and second holds the frame data
        raw_timestamp = float(row[0])
        if first_timestamp is None:
            first_timestamp = raw_timestamp
        timestamp = raw_timestamp - first_timestamp
        if last_timestamp is not None:
            plt.pause((timestamp - last_timestamp) / speed_up_factor)
        last_timestamp = timestamp
        frame_data = row[1]
        print(f"Timestamp: {timestamp}")
        print(frame_data)

        # Processing the frame data
        frame = [float(j) for j in frame_data.replace('[', '').replace(']', '').split(',')]
        avg_value = np.mean(frame)
        frame = [avg_value if x < 0 else x for x in frame]

        diff = np.array(frame) - np.array(last_frame)
        last_frame = frame

        if diff_mode:
            frame = diff

        # Reshape and update the thermal image
        data_array = np.reshape(frame, (24, 32))
        therm1.set_data(np.fliplr(data_array))

        # Keep the color scale constant across frames
        therm1.set_clim(vmin=vmin, vmax=vmax)

        # Update the subtitle with the timestamp
        plt.suptitle(f"Timestamp: {timestamp}", fontsize=16)

        # Redraw the figure to update the plot, colorbar, and title
        fig.canvas.draw()
        fig.canvas.flush_events()
