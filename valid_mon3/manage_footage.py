import os
import re
import shutil
import cv2
import json
import pandas as pd
from tqdm import tqdm
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog

TEST_MODE = True
UNDO_FILE = "undo_renames.json"

ALLOWED_EXTENSIONS = [".mp4", ".ts"]
VALID_DURATIONS = [(530, 670), (230, 370)]
CAM_PATTERN = re.compile(r"CAM\d+")
FILENAME_PATTERN = re.compile(r"(CAM\d+)_(\d{8})_(\d{4,6})\.(mp4|ts)")

def select_directory():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory(title="Select the REC folder")

def parse_filename(filename):
    match = FILENAME_PATTERN.match(filename)
    if match:
        cam, date_str, time_str, ext = match.groups()
        time_str = time_str.ljust(6, '0')
        return cam, date_str, time_str, ext
    return None

def get_video_duration(path):
    try:
        video = cv2.VideoCapture(path)
        if video.isOpened():
            frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
            fps = video.get(cv2.CAP_PROP_FPS)
            return frames / fps if fps > 0 else 0
    finally:
        video.release()
    return 0

def is_valid_duration(duration):
    return any(low <= duration <= high for (low, high) in VALID_DURATIONS)

def scan_and_validate_files(rec_path, run_stamp):
    all_valid_files = []
    camera_names = set()
    undo_actions = []
    change_log = {}

    for cam_folder in os.listdir(rec_path):
        if not CAM_PATTERN.fullmatch(cam_folder):
            continue

        cam_path = os.path.join(rec_path, cam_folder)
        if not os.path.isdir(cam_path):
            continue

        camera_names.add(cam_folder)
        corrupted_path = os.path.join(cam_path, "corrupted")
        renamed_path = os.path.join(cam_path, "renamed")
        unmatched_path = os.path.join(cam_path, "unmatched")
        os.makedirs(corrupted_path, exist_ok=True)
        os.makedirs(renamed_path, exist_ok=True)
        os.makedirs(unmatched_path, exist_ok=True)

        log_path = os.path.join(cam_path, f"change_log_{run_stamp}.txt")
        change_log[cam_folder] = {"log_path": log_path, "entries": [], "unmatched": []}

        for filename in tqdm(os.listdir(cam_path), desc=f"Scanning {cam_folder}", ncols=None):
            full_path = os.path.join(cam_path, filename)
            if not os.path.isfile(full_path):
                continue
            if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                continue

            parsed = parse_filename(filename)
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not parsed:
                reason = f"{now_str} | Invalid filename format"
                if not TEST_MODE:
                    shutil.move(full_path, os.path.join(corrupted_path, filename))
                change_log[cam_folder]["entries"].append(f"Corrupted: {filename} → {reason}")
                continue

            cam, date_str, time_str, ext = parsed
            duration = get_video_duration(full_path)

            if not is_valid_duration(duration):
                reason = f"{now_str} | Invalid duration: {duration:.2f}s"
                if not TEST_MODE:
                    shutil.move(full_path, os.path.join(corrupted_path, filename))
                change_log[cam_folder]["entries"].append(f"Corrupted: {filename} → {reason}")
                continue

            if len(time_str) == 4:
                try:
                    end_time = datetime.fromtimestamp(os.path.getmtime(full_path))
                    start_time = end_time - timedelta(seconds=duration)
                    time_str = start_time.strftime("%H%M%S")
                    new_filename = f"{cam}_{date_str}_{time_str}.{ext}"
                    new_path = os.path.join(cam_path, new_filename)

                    if os.path.exists(new_path):
                        print(f"Skipping (already exists): {new_filename}")
                        continue

                    if TEST_MODE:
                        print(f"[TEST] Would copy {filename} → {new_filename}")
                        print(f"[TEST] Would move {filename} → renamed/")
                    else:
                        shutil.copy2(full_path, new_path)
                        shutil.move(full_path, os.path.join(renamed_path, filename))
                        change_log[cam_folder]["entries"].append(
                            f"Renamed: {filename} → {new_filename} | Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')} | Duration: {int(duration)}s"
                        )
                        undo_actions.append({
                            "new_file": new_path,
                            "original_file": full_path,
                            "moved_original": os.path.join(renamed_path, filename),
                        })

                    filename = new_filename
                    full_path = new_path

                except Exception as e:
                    reason = f"{now_str} | Exception during rename: {e}"
                    if not TEST_MODE:
                        shutil.move(full_path, os.path.join(corrupted_path, filename))
                    change_log[cam_folder]["entries"].append(f"Corrupted: {filename} → {reason}")
                    continue

            all_valid_files.append({
                "camera": cam,
                "date": date_str,
                "time": time_str,
                "filename": filename,
                "path": full_path,
            })

    if not TEST_MODE and undo_actions:
        with open(os.path.join(rec_path, UNDO_FILE), "w", encoding="utf-8") as f:
            json.dump(undo_actions, f, indent=2)

    return all_valid_files, camera_names, change_log

def find_and_handle_unmatched(valid_files, camera_names, change_log):
    grouped = {}
    for f in valid_files:
        key = f"{f['date']}_{f['time']}"
        grouped.setdefault(key, []).append(f)

    unmatched = []
    for key, files in grouped.items():
        cams_present = {f["camera"] for f in files}
        if cams_present != camera_names:
            unmatched.append((key, cams_present))
            for f in files:
                cam = f["camera"]
                if not TEST_MODE:
                    unmatched_path = os.path.join(os.path.dirname(f["path"]), "unmatched")
                    shutil.move(f["path"], os.path.join(unmatched_path, f["filename"]))
                change_log[cam]["unmatched"].append((key, sorted(cams_present)))

    matched = [f for f in valid_files if (f"{f['date']}_{f['time']}", set(camera_names)) not in unmatched]
    return matched, unmatched

def export_csv(valid_files, output_dir, camera_names):
    grouped = {}
    for f in valid_files:
        key = f"{f['date']}_{f['time']}"
        grouped.setdefault(key, []).append(f)

    rows = []
    for key, files in grouped.items():
        if len(files) == len(camera_names):
            date_str, time_str = key.split("_")
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
            rows.append([formatted_date, formatted_time, files[0]["filename"]])

    df = pd.DataFrame(rows, columns=["Date (YYYY-MM-DD)", "Time (HH:MM:SS)", "Filename"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"footage_timestamps_{timestamp}.csv")

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        df.to_csv(f, index=False)

    return output_path

def undo_renames(rec_path):
    undo_path = os.path.join(rec_path, UNDO_FILE)
    if not os.path.exists(undo_path):
        print("No undo file found.")
        return

    with open(undo_path, "r", encoding="utf-8") as f:
        actions = json.load(f)

    for entry in actions:
        try:
            if os.path.exists(entry["new_file"]):
                os.remove(entry["new_file"])
            if os.path.exists(entry["moved_original"]):
                shutil.move(entry["moved_original"], entry["original_file"])
            print(f"Undid: {os.path.basename(entry['new_file'])}")
        except Exception as e:
            print(f"Failed to undo {entry['new_file']}: {e}")

def main():
    rec_path = select_directory()
    print(f"\nFolder selected: {rec_path}")

    undo_path = os.path.join(rec_path, UNDO_FILE)
    if os.path.exists(undo_path):
        undo_choice = input("\nUndo last rename operation? (y/n): ").strip().lower()
        if undo_choice == "y":
            undo_renames(rec_path)
            return

    dry_choice = input("\nRun in dry mode first? (y/n): ").strip().lower()
    dry_mode = dry_choice != "n"
    global TEST_MODE
    TEST_MODE = dry_mode

    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    valid_files, camera_names, change_log = scan_and_validate_files(rec_path, run_stamp)

    if TEST_MODE:
        apply_choice = input("\nDry run complete. Apply renames and generate CSV? (y/n): ").strip().lower()
        if apply_choice == "y":
            TEST_MODE = False
            print("\nApplying changes...")
            valid_files, camera_names, change_log = scan_and_validate_files(rec_path, run_stamp)
        else:
            print("\nNo changes made. Exiting.")
            return

    matched_files, unmatched_info = find_and_handle_unmatched(valid_files, camera_names, change_log)
    csv_path = export_csv(matched_files, rec_path, camera_names)

    for cam, data in change_log.items():
        with open(data["log_path"], "w", encoding="utf-8") as log:
            log.write(f"Camera: {cam}\n")
            for entry in data["entries"]:
                log.write(f"{entry}\n")
            if data["unmatched"]:
                log.write("\nUnmatched Timestamps:\n")
                for key, present in data["unmatched"]:
                    formatted = f"{key[:4]}-{key[4:6]}-{key[6:8]} {key[9:11]}:{key[11:13]}:{key[13:]}"
                    log.write(f"  {formatted} | Present in: {', '.join(present)}\n")

    master_log_path = os.path.join(rec_path, f"master_log_{run_stamp}.txt")
    with open(master_log_path, "w", encoding="utf-8") as log:
        log.write(f"==== Run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====\n\n")
        for cam, data in change_log.items():
            log.write(f"{cam}:\n")
            for entry in data["entries"]:
                log.write(f"  {entry}\n")
            if data["unmatched"]:
                log.write("  Unmatched:\n")
                for key, present in data["unmatched"]:
                    formatted = f"{key[:4]}-{key[4:6]}-{key[6:8]} {key[9:11]}:{key[11:13]}:{key[13:]}"
                    log.write(f"    {formatted} | Present in: {', '.join(present)}\n")
            log.write("\n")
        log.write(f"CSV: {os.path.basename(csv_path)}\n")

    print(f"\nSummary written to: {master_log_path}")
    print("\nTerminal Summary:\n")
    for cam, data in change_log.items():
        print(f"{cam}")
        if data["entries"]:
            for entry in data["entries"]:
                print(f"  {entry}")
        else:
            print("  (No renames or corrupted files)")
        if data["unmatched"]:
            print("  Unmatched Timestamps:")
            for key, present in data["unmatched"]:
                formatted = f"{key[:4]}-{key[4:6]}-{key[6:8]} {key[9:11]}:{key[11:13]}:{key[13:]}"
                print(f"    {formatted} | Present in: {', '.join(present)}")
        print()

if __name__ == "__main__":
    main()
