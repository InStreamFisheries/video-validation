# manage_footage.py
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import shutil
import cv2
from datetime import datetime
from tqdm import tqdm

# pick REC folder
root = tk.Tk()
root.withdraw() 
rec_directory_path = filedialog.askdirectory(title = "Select the REC folder")

# checking for corruptions in cam folders
def check_for_corruptions(rec_directory_path):
    print("Scanning REC folder for CAM folders...")
    for cam_folder in os.listdir(rec_directory_path):
        cam_folder_path = os.path.join(rec_directory_path, cam_folder)
        if os.path.isdir(cam_folder_path) and cam_folder.startswith("CAM"):
            corrupted_folder_path = os.path.join(cam_folder_path, "corrupted")
            if not os.path.exists(corrupted_folder_path):
                os.makedirs(corrupted_folder_path)
            
            print(f"Scanning {cam_folder} for video files...")
            filenames = [f for f in os.listdir(cam_folder_path) if f.startswith(f"{cam_folder}_") and f.endswith(".mp4")]
            
            for filename in tqdm(filenames, desc=f"Scanning {cam_folder}", ncols=None):
                file_path = os.path.join(cam_folder_path, filename)
                
                # check if the file is corrupted or not the expected length
                try:
                    video = cv2.VideoCapture(file_path)
                    if video.isOpened():
                        frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
                        fps = video.get(cv2.CAP_PROP_FPS)
                        duration = frames / fps if fps > 0 else 0
                        # around 10 minutes (600 seconds, give or take 1m (60s))
                        if not (540 <= duration <= 660):
                            shutil.move(file_path, os.path.join(corrupted_folder_path, filename))
                            print(f"\nMoved corrupted or incorrect length file: {filename}")
                    else:
                        shutil.move(file_path, os.path.join(corrupted_folder_path, filename))
                        print(f"\nMoved corrupted file: {filename}")
                except Exception as e:
                    shutil.move(file_path, os.path.join(corrupted_folder_path, filename))
                    print(f"\nMoved file due to error ({e}): {filename}")
                finally:
                    video.release()
            
            print(f"Finished scanning {cam_folder}.")

# create timestamps CSV for CAM1
def create_timestamps_csv(rec_directory_path):
    data = []
    cam1_folder_path = os.path.join(rec_directory_path, "CAM1")
    if os.path.isdir(cam1_folder_path):
        print("Scanning files to create timestamps...")
        filenames = [f for f in os.listdir(cam1_folder_path) if f.startswith("CAM1_") and f.endswith(".mp4")]
        
        for filename in tqdm(filenames, desc="Creating timestamps", ncols=None):
            file_path = os.path.join(cam1_folder_path, filename)
            
            # extract date and time
            parts = filename.split("_")
            date_str = parts[1]  # YYYYMMDD
            time_str = parts[2].replace(".mp4", "")
            date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            time_formatted = f"{time_str[:2]}:{time_str[2:]}"
            
            data.append([date_formatted, time_formatted])

    # create a DataFrame and save it to a CSV file
    if data:
        df = pd.DataFrame(data, columns=["Date (YYYY-MM-DD)", "Time (HH:MM)"])
        df["Date (YYYY-MM-DD)"] = df["Date (YYYY-MM-DD)"].astype(str)
        current_date_str = datetime.now().strftime("%Y%m%d_%H%M")
        output_path = os.path.join(rec_directory_path, f"timestamps_{current_date_str}.csv")
        df.to_csv(output_path, index=False)
        print(f"Timestamps saved to {output_path}")
    else:
        print("No valid files found.")

# run the corruption check and timestamp creation
check_for_corruptions(rec_directory_path)
create_timestamps_csv(rec_directory_path)
