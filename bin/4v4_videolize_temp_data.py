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
parser.add_argument("folder", type=str, help="Name of folder that contains csv files to be processed")
parser.add_argument(
    "-s", "--speed", default=1, type=int, help="Speed the video will be in"
)
parser.add_argument("--min", type=int, help="Minimum value for the color scale")
parser.add_argument("--max", type=int, help="Maximum value for the color scale")

args = parser.parse_args()
speed_up_factor = args.speed

# Create a temporary directory to hold frames
temp_dir = tempfile.mkdtemp()

vmin = -25
vmax = 90

if args.min:
    vmin = args.min
if args.max:
    vmax = args.max

fileNames = os.listdir(args.folder);


first_timestamp = None
last_timestamp = None


frames_txt_path = os.path.join(temp_dir, "frames_timestamps.txt")
line_num = 0

piIds = [f[-5:-4] for f in fileNames if f.endswith(".csv")]
files = [open(os.path.join(args.folder, f)) for f in fileNames if f.endswith(".csv")]

def get_next_frame(reader):
    while True:
        row = next(reader, None)
        if row is None:
            return None
        if len(row) > 0 and row[1] == "tire_temp_frame":
            return row

readers = [csv.reader(f) for f in files]
[next(reader) for reader in readers] # Skip header

frames = [get_next_frame(reader) for reader in readers]

kill = []
for i in range(len(frames)):
    if frames[i] is None:
        kill.append(i)
    else:
        continue

for i in kill:
    files[i].close()
    frames.pop(i)
    readers.pop(i)
    files.pop(i)
    piIds.pop(i)

first_timestamp = min([datetime.fromisoformat(frame[0]) for frame in frames])

def render(timestamp, frames, duration):
    fig, axs = plt.subplots(2,2)

    for i in range(len(frames)):
        ax = axs[i//2][i%2]
        plt.subplot(2, 2, i + 1)
        therm1 = ax.imshow(np.zeros((24, 32)), vmin=vmin, vmax=vmax, cmap="coolwarm")
        ax.set_title("Thermal Camera Data")
        frame_data = frames[i][2]
        if frame_data.strip() == "":
            print("Empty line. Skipping")
            continue
        frame = None
        try:
            frame = [
                int(j)/100
                for j in frame_data.replace("[", "").replace("]", "").replace("'", "").split(",")
            ]
        except Exception as e:
            print(f"Error parsing frame data on line {line_num}: {e}")
            print(frame_data)
            print(frame_data.replace("[", "").replace("]", "").replace("'", ""))
            continue

        avg_value = np.mean(frame)
        frame = [avg_value if x < 0 else x for x in frame]

        data_array = np.reshape(frame, (24, 32))
        therm1.set_data(np.fliplr(data_array))
        therm1.set_clim(vmin=vmin, vmax=vmax)

    plt.suptitle(f"Timestamp: {smallest}", fontsize=16)
    frame_file_name = os.path.join(
        temp_dir, f"frame_{int(smallest.timestamp() * 100)}.png"
    )
    fig.savefig(frame_file_name)
    timestamp_file.write(
        f"file '{frame_file_name}'\nduration {duration/speed_up_factor}\n"
    )
    plt.close(fig)

with open(frames_txt_path, "w") as timestamp_file:
    timestamps = [datetime.fromisoformat(frame[0]) for frame in frames]

    # Find the index of the smallest timestamp

    while True:
        validTimestamps = [t for t in timestamps if t is not None]
        if len(validTimestamps) == 0:
            break
        smallest = min(validTimestamps)
        smallestIndex = timestamps.index(smallest)
        next_frame = get_next_frame(readers[smallestIndex])
        if next_frame is None:
            timestamps[smallestIndex] = None
        else:
            timestamps[smallestIndex] = datetime.fromisoformat(next_frame[0])

        validTimestamps = [t for t in timestamps if t is not None]
        next_timestamp = None if len(validTimestamps) == 0 else min([t for t in timestamps if t is not None])
        duration = max(0.01, 1 if next_timestamp == None else (next_timestamp - smallest).total_seconds())

        render(smallest, frames, duration)

        if next_frame is not None:
            frames[smallestIndex] = next_frame

#     if first_timestamp is None:
#         first_timestamp = raw_timestamp
#     timestamp = (raw_timestamp - first_timestamp).total_seconds()

#     progress_percent = (line_num / total_lines) * 100
#     print(
#         f"{progress_percent:.1f}% Processing line {line_num} - time {timestamp:.1f}",
#         end="\r",
#     )

#     if last_timestamp is not None:
#         gap = timestamp - last_timestamp
#         frame_duration = max(gap / speed_up_factor, 0.05)
#     else:
#         frame_duration = 0.05 / speed_up_factor

#     last_timestamp = timestamp
#     frame_data = row[1]
#     if frame_data.strip() == "":
#         print("Empty line. Skipping")
#         continue
#     frame = None
#     try:
#         frame = [
#             float(j)
#             for j in frame_data.replace("[", "").replace("]", "").replace("'", "").split(",")
#         ]
#     except Exception as e:
#         print(f"Error parsing frame data on line {line_num}: {e}")
#         print(frame_data)
#         print(frame_data.replace("[", "").replace("]", "").replace("'", ""))
#         continue
#     avg_value = np.mean(frame)
#     frame = [avg_value if x < 0 else x for x in frame]


#     if diff_mode:
#         frame = diff

#     data_array = np.reshape(frame, (24, 32))
#     therm1.set_data(np.fliplr(data_array))
#     therm1.set_clim(vmin=vmin, vmax=vmax)

#     plt.suptitle(f"Timestamp: {timestamp:.1f}", fontsize=16)
#     frame_file_name = os.path.join(
#         temp_dir, f"frame_{int(timestamp * 100)}.png"
#     )
#     fig.savefig(frame_file_name)

#     timestamp_file.write(
#         f"file '{frame_file_name}'\nduration {frame_duration}\n"
#     )

script_dir = os.path.dirname(os.path.realpath(__file__))
output_video_name = os.path.join(
    script_dir,
    f"../videos/{os.path.splitext(os.path.basename(args.folder))[0]}_{speed_up_factor}x.mp4",
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
