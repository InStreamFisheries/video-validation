import os
import pandas as pd
from datetime import datetime, timedelta
from tkinter import filedialog
import tkinter as tk

# GUI to select the REC folder
root = tk.Tk()
root.withdraw()
rec_directory_path = filedialog.askdirectory(title="Select the REC folder")

# GUI to select the existing timestamps CSV file
timestamps_csv_path = filedialog.askopenfilename(title="Select the timestamps CSV file", filetypes=[("CSV files", "*.csv")])

def update_timestamps_with_difference(rec_directory_path, timestamps_csv_path):
    # Load the CSV and ensure time values are strings
    df = pd.read_csv(timestamps_csv_path, dtype={"Time (HH:MM)": str})

    # Columns for start times and time differences
    start_times = []
    time_differences = []

    # Iterate through each row in the CSV
    for index, row in df.iterrows():
        date_str = str(row["Date (YYYY-MM-DD)"]).strip()
        time_str = str(row["Time (HH:MM)"]).strip()

        # Construct video filename using time (HHMM)
        time_part = time_str.replace(":", "")[:4]  # Get HHMM format
        filename = f"CAM2_{date_str.replace('-', '')}_{time_part}.mp4"
        file_path = os.path.join(rec_directory_path, "CAM2", filename)

        if os.path.exists(file_path):
            # Get the modification time of the file (end time of the recording)
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))

            # Calculate start time (10 minutes before the end time)
            start_time = modified_time - timedelta(seconds=600)

            # Calculate time difference
            actual_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            time_difference = abs((actual_time - start_time).total_seconds())

            # Convert time difference to MM:SS format
            minutes, seconds = divmod(int(time_difference), 60)
            time_differences.append(f"{minutes:02}:{seconds:02}")

            # Append the start time
            start_times.append(start_time.strftime("%H:%M:%S"))
        else:
            # If the file is not found, record this in the output
            start_times.append("File not found")
            time_differences.append("N/A")

    # Add the new columns to the DataFrame
    df["Start Time"] = start_times
    df["Time Difference"] = time_differences

    # Save the updated CSV
    output_path = timestamps_csv_path.replace(".csv", "_updated.csv")
    df.to_csv(output_path, index=False)
    print(f"Updated timestamps saved to {output_path}")

# Run the update
update_timestamps_with_difference(rec_directory_path, timestamps_csv_path)
