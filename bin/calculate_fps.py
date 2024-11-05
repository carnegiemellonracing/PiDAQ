from datetime import datetime

import pandas as pd

paths = [
    # "../rasppi/tests/2024_11_03/lowframeratetest2---1730615089099/01_24_lowframeratetest2---1730615089099_PI0.csv",
    # "../rasppi/tests/2024_11_03/lowframeratetest2---1730615089099/01_24_lowframeratetest2---1730615089099_PI1.csv",
    # "../rasppi/tests/2024_11_03/lowframeratetest2---1730615089099/01_24_lowframeratetest2---1730615089099_PI2.csv",
    # "../rasppi/tests/2024_11_03/lowframeratetest2---1730615089099/01_24_lowframeratetest2---1730615089099_PI3.csv",
    #
    "../rasppi/tests/2024_11_01/New test blablabla---1730437232487/01_00_New test blablabla---1730437232487_PI0.csv",
    "../rasppi/tests/2024_11_01/oliver1---1730470754820/10_19_oliver1---1730470754820_PI0.csv",
    "../rasppi/tests/2024_11_01/lana-1---1730471169444/10_26_lana-1---1730471169444_PI0.csv",
    "../rasppi/tests/2024_11_01/dry-run-fuckass---1730476543537/11_55_dry-run-fuckass---1730476543537_PI0.csv",
    "../rasppi/tests/2024_11_01/testagain---1730477407558/12_10_testagain---1730477407558_PI0.csv",
    "../rasppi/tests/2024_11_01/test???---1730477421750/12_10_test???---1730477421750_PI0.csv",
    "../rasppi/tests/2024_11_01/long_test_start_1_09_quintin_r---1730480957920/13_09_long_test_start_1_09_quintin_r---1730480957920_PI0.csv",
    "../rasppi/tests/2024_11_01/chris---1730484580194/14_09_chris---1730484580194_PI0.csv",
    "../rasppi/tests/2024_11_01/oliver---1730485526982/14_25_oliver---1730485526982_PI0.csv",
    # "../rasppi/tests/2024_11_01/oliver1---1730470754820/10_19_oliver1---1730470754820_PI2.csv",
    # "../rasppi/tests/2024_11_01/oliver1---1730470754820/10_23_oliver1---1730470754820_PI1.csv",
    # "../rasppi/tests/2024_11_01/oliver1---1730470754820/10_25_oliver1---1730470754820_PI3.csv",
    #
    # "../rasppi/tests/2024_11_01/test???---1730477421750/12_10_test???---1730477421750_PI1.csv",
    # "../rasppi/tests/2024_11_01/test???---1730477421750/12_10_test???---1730477421750_PI2.csv",
    # "../rasppi/tests/2024_11_01/test???---1730477421750/12_10_test???---1730477421750_PI3.csv",
    #
    # "../rasppi/tests/2024_11_01/chris---1730484580194/14_09_chris---1730484580194_PI1.csv",
    # "../rasppi/tests/2024_11_01/chris---1730484580194/14_09_chris---1730484580194_PI2.csv",
    # "../rasppi/tests/2024_11_01/chris---1730484580194/14_09_chris---1730484580194_PI3.csv",
    #
    # "../rasppi/tests/2024_11_01/oliver---1730485526982/14_25_oliver---1730485526982_PI1.csv",
    # "../rasppi/tests/2024_11_01/oliver---1730485526982/14_25_oliver---1730485526982_PI2.csv",
    # "../rasppi/tests/2024_11_01/oliver---1730485526982/14_25_oliver---1730485526982_PI3.csv",
    #
    # "../rasppi/tests/2024_11_01/quintin-longtest---1730482133717/13_28_quintin-longtest---1730482133717_PI0.csv",
    # "../rasppi/tests/2024_11_01/quintin-longtest---1730482133717/13_28_quintin-longtest---1730482133717_PI1.csv",
    # "../rasppi/tests/2024_11_01/quintin-longtest---1730482133717/13_28_quintin-longtest---1730482133717_PI2.csv",
    # "../rasppi/tests/2024_11_01/quintin-longtest---1730482133717/13_28_quintin-longtest---1730482133717_PI3.csv",
    #
    # "../rasppi/tests/2024_11_01/lana-1---1730471169444/10_26_lana-1---1730471169444_PI1.csv",
    # "../rasppi/tests/2024_11_01/lana-1---1730471169444/10_26_lana-1---1730471169444_PI2.csv",
    # "../rasppi/tests/2024_11_01/lana-1---1730471169444/10_26_lana-1---1730471169444_PI3.csv",
]


for i, file_path in enumerate(paths):
    # Load the CSV file to examine its structure
    data = pd.read_csv(file_path)

    # Display the first few rows to understand its structure
    data.head()

    # Filter rows that likely represent individual frames by checking the presence of 'tire_temp_frame' in the second column
    frame_data = data[data["tire_temp_frame"] == "tire_temp_frame"]

    # Convert timestamp strings to datetime objects for these rows
    timestamps = pd.to_datetime(frame_data["timestamp"])

    # Calculate the time differences between consecutive frames
    time_diffs = timestamps.diff().dropna().dt.total_seconds()

    # Calculate FPS as the reciprocal of the average time difference
    fps = 1 / time_diffs.mean()
    print(f"Pi#{i} | FPS: {fps}")
