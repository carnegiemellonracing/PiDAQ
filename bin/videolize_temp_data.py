import time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
import csv
import os
import subprocess
import shutil
import tempfile
import argparse

parser = argparse.ArgumentParser(description="Process CLI arguments.")

parser.add_argument("file_name", type=str, help="Name of csv file to be processed")
parser.add_argument("-s", "--speed", default=1, type=int,help="Speed the video will be in")
parser.add_argument("-d", "--diff", action="store_true", help="Mode to show the difference between frames")
parser.add_argument("--min", type=int, help="Minimum value for the color scale")
parser.add_argument("--max", type=int, help="Maximum value for the color scale")

args = parser.parse_args()
file_name = args.file_name
speed_up_factor = args.speed
diff_mode = args.diff

# Create a temporary directory to hold frames
temp_dir = tempfile.mkdtemp()

# plt.ion()
fig, ax = plt.subplots(figsize=(12, 7))

# Set a constant scale (vmin, vmax) and use a blue-to-red gradient (coolwarm colormap)
vmin = -30 if diff_mode else 25  # Set your desired minimum value for the color scale
vmax = 30 if diff_mode else 90  # Set your desired maximum value for the color scale

if args.min:
    vmin = args.min

if args.max:
    vmax = args.max

therm1 = ax.imshow(np.zeros((24, 32)), vmin=vmin, vmax=vmax, cmap='coolwarm')

cbar = fig.colorbar(therm1)
cbar.set_label('Temperature [$^{\circ}$C]', fontsize=14)

first_timestamp = None
last_timestamp = None
last_frame = np.zeros(24 * 32)

# Set a title for the plot
ax.set_title('Thermal Camera Data')

# Path for the frames_timestamps.txt file
frames_txt_path = os.path.join(temp_dir, 'frames_timestamps.txt')

line_num = 0

# Open a file to save frame durations
with open(frames_txt_path, 'w') as timestamp_file:
    #  run  `wc -l filename` (very long file. Be careful)

    total_lines = sum(1 for line in open(file_name))
    with open(file_name, 'r') as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip the header row

        for row in reader:
            line_num += 1
            if(row[0] == "timestamp"):
                # Not a number, repeating csv headers
                continue
            raw_timestamp = float(row[0])
            if first_timestamp is None:
                first_timestamp = raw_timestamp
            timestamp = raw_timestamp - first_timestamp

            progress_percent = (line_num / total_lines) * 100
            formatted_percent = "{:.1f}%".format(progress_percent)
            formatted_timestamp = "{:.1f}".format(timestamp)

            print(f"{formatted_percent} Processing line {line_num} - time {formatted_timestamp}", end='\r')

            if last_timestamp is not None:
                gap = timestamp - last_timestamp
                if gap > 1:
                    print(f"Warning: large gap detected between frames. This may cause stuttering in the video. FRAME = #{line_num} - TIME = {timestamp} - GAP = {gap}")

                if gap < 0:
                    print(f"Warning: negative gap detected between frames. This SHOULD NOT HAPPEN. FRAME = #{line_num} - TIME = {timestamp} - GAP = {gap}")

                frame_duration = max(gap / speed_up_factor, 0.05)

            else:
                frame_duration = 0.05 / speed_up_factor  # Set a small default duration for the first frame

            last_timestamp = timestamp
            frame_data = row[1]

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
            plt.suptitle(f"Timestamp: {timestamp:.1f}", fontsize=16)

            # Redraw the figure to update the plot, colorbar, and title
            # fig.canvas.draw()
            # fig.canvas.flush_events()

            # Save the current frame as an image file
            frame_file_name = os.path.join(temp_dir, f'frame_{int(timestamp * 100)}.png')
            fig.savefig(frame_file_name)

            # Write the frame and its corresponding duration to the file
            timestamp_file.write(f"file '{frame_file_name}'\nduration {frame_duration}\n")

# Run ffmpeg command to create the video from frames
script_dir = os.path.dirname(os.path.realpath(__file__))
file_name = os.path.splitext(os.path.basename(file_name))[0]
file_name += f"_{speed_up_factor}x"
if diff_mode:
    file_name += "_diff"
if args.min or args.max:
    file_name += f"_{args.min}-{args.max}"

file_name += ".mp4"

output_video_name = os.path.join(script_dir,f"../videos/{file_name}")
output_directory = os.path.dirname(output_video_name)
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

ffmpeg_cmd = [
    'ffmpeg', '-f', 'concat', '-safe', '0', '-i', frames_txt_path,
    '-vsync', 'vfr', '-pix_fmt', 'yuv420p', output_video_name
]

print("Running ffmpeg to create the video...")
subprocess.run(ffmpeg_cmd, check=True)

# Clean up the temporary directory and files
shutil.rmtree(temp_dir)
print(f"Video created: {output_video_name}")
print("Temporary files cleaned up.")
