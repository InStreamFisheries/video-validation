import os
import pandas as pd
import shutil
from tqdm import tqdm
import tkinter as tk
from tkinter import filedialog


def main():
    root = tk.Tk()
    root.withdraw()
    rec_directory_path = filedialog.askdirectory(title="Select the REC directory")
    if not rec_directory_path or not os.path.isdir(rec_directory_path):
        print("Invalid directory path.")
        return

    csv_file_path = filedialog.askopenfilename(title="Select the sampled_timestamps CSV file", filetypes=[("CSV files", "*.csv")])
    if not csv_file_path or not os.path.isfile(csv_file_path):
        print("Invalid CSV file path.")
        return

    df = pd.read_csv(csv_file_path, dtype={'Date (YYYY-MM-DD)': str, 'Time (HH:MM)': str})
    df['Time (HH:MM)'] = df['Time (HH:MM)'].str[:5]
    df['Combined_Timestamp'] = df['Date (YYYY-MM-DD)'].str.replace('-', '') + '_' + df['Time (HH:MM)'].str.replace(':', '')
    valid_timestamps = set(df['Combined_Timestamp'].tolist())
    print("Valid timestamps from CSV:")
    print(valid_timestamps)

    for cam_folder in tqdm(os.listdir(rec_directory_path), desc="Scanning CAM folders"):
        cam_folder_path = os.path.join(rec_directory_path, cam_folder)
        if os.path.isdir(cam_folder_path) and cam_folder.startswith("CAM"):
            # 'moved' subfolder in the CAMX folder to move non-matching files
            moved_folder_path = os.path.join(cam_folder_path, "moved")
            if not os.path.exists(moved_folder_path):
                os.makedirs(moved_folder_path)

            video_files = [f for f in os.listdir(cam_folder_path) if f.endswith(".mp4")]
            for filename in tqdm(video_files, desc=f"Processing files in {cam_folder}"):
                if filename.startswith(f"{cam_folder}_") and filename.endswith(".mp4"):
                    parts = filename.split("_")
                    if len(parts) == 3:
                        date_str = parts[1]  # YYYYMMDD
                        time_str = parts[2].replace(".mp4", "")  # HHMM
                        combined_timestamp = f"{date_str}_{time_str}"
                        print(f"Checking file: {filename}, extracted timestamp: {combined_timestamp}")
                        if combined_timestamp not in valid_timestamps:
                            print(f"Moving file: {filename} (timestamp not in valid timestamps)")
                            shutil.move(os.path.join(cam_folder_path, filename), os.path.join(moved_folder_path, filename))
                        else:
                            print(f"Keeping file: {filename} (timestamp is valid)")

if __name__ == "__main__":
    main()
