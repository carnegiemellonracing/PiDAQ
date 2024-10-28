import time
import numpy as np
import matplotlib
from datetime import datetime

matplotlib.use("Agg")
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
parser.add_argument(
    "-s", "--speed", default=1, type=int, help="Speed the video will be in"
)
parser.add_argument(
    "-d",
    "--diff",
    action="store_true",
    help="Mode to show the difference between frames",
)
parser.add_argument("--min", type=int, help="Minimum value for the color scale")
parser.add_argument("--max", type=int, help="Maximum value for the color scale")

args = parser.parse_args()
file_name = args.file_name
speed_up_factor = args.speed
diff_mode = args.diff

# Create a temporary directory to hold frames
temp_dir = tempfile.mkdtemp()

fig, ax = plt.subplots(figsize=(12, 7))
vmin = -30 if diff_mode else 25
vmax = 30 if diff_mode else 90
if args.min:
    vmin = args.min
if args.max:
    vmax = args.max

therm1 = ax.imshow(np.zeros((24, 32)), vmin=vmin, vmax=vmax, cmap="coolwarm")
cbar = fig.colorbar(therm1)
cbar.set_label("Temperature [$^{\circ}$C]", fontsize=14)

first_timestamp = None
last_timestamp = None
last_frame = np.zeros(24 * 32)
ax.set_title("Thermal Camera Data")

frames_txt_path = os.path.join(temp_dir, "frames_timestamps.txt")
line_num = 0

with open(frames_txt_path, "w") as timestamp_file:
    total_lines = sum(1 for _ in open(file_name))
    with open(file_name, "r") as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip header

        for row in reader:
            line_num += 1
            try:
                raw_timestamp = datetime.fromisoformat(row[0])
            except ValueError as e:
                print(f"Error parsing timestamp on line {line_num}: {e}")
                continue

            if first_timestamp is None:
                first_timestamp = raw_timestamp
            timestamp = (raw_timestamp - first_timestamp).total_seconds()

            progress_percent = (line_num / total_lines) * 100
            print(
                f"{progress_percent:.1f}% Processing line {line_num} - time {timestamp:.1f}",
                end="\r",
            )

            if last_timestamp is not None:
                gap = timestamp - last_timestamp
                frame_duration = max(gap / speed_up_factor, 0.05)
            else:
                frame_duration = 0.05 / speed_up_factor

            last_timestamp = timestamp
            frame_data = row[1]
            if frame_data.strip() == "":
                print("Empty line. Skipping")
                continue
            frame = None
            try:
                frame = [
                    float(j)
                    for j in frame_data.replace("[", "").replace("]", "").replace("'", "").split(",")
                ]
            except Exception as e:
                print(f"Error parsing frame data on line {line_num}: {e}")
                print(frame_data)
                print(frame_data.replace("[", "").replace("]", "").replace("'", ""))
                continue
            avg_value = np.mean(frame)
            frame = [avg_value if x < 0 else x for x in frame]

            diff = np.array(frame) - np.array(last_frame)
            last_frame = frame

            if diff_mode:
                frame = diff

            data_array = np.reshape(frame, (24, 32))
            therm1.set_data(np.fliplr(data_array))
            therm1.set_clim(vmin=vmin, vmax=vmax)

            plt.suptitle(f"Timestamp: {timestamp:.1f}", fontsize=16)
            frame_file_name = os.path.join(
                temp_dir, f"frame_{int(timestamp * 100)}.png"
            )
            fig.savefig(frame_file_name)

            timestamp_file.write(
                f"file '{frame_file_name}'\nduration {frame_duration}\n"
            )

script_dir = os.path.dirname(os.path.realpath(__file__))
output_video_name = os.path.join(
    script_dir,
    f"../videos/{os.path.splitext(os.path.basename(file_name))[0]}_{speed_up_factor}x.mp4",
)
os.makedirs(os.path.dirname(output_video_name), exist_ok=True)

ffmpeg_cmd = [
    "ffmpeg",
    "-f",
    "concat",
    "-safe",
    "0",
    "-i",
    frames_txt_path,
    "-vsync",
    "vfr",
    "-pix_fmt",
    "yuv420p",
    output_video_name,
]
print("Running ffmpeg to create the video...")
subprocess.run(ffmpeg_cmd, check=True)

shutil.rmtree(temp_dir)
print(f"Video created: {output_video_name}")
