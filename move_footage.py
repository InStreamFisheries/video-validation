import os
import csv
import shutil
from pathlib import Path
from tkinter import Tk, filedialog
from collections import defaultdict
from datetime import datetime

CONFIG_FILE = Path("config.txt")

def extract_timestamps(csv_path):
    timestamps = set()
    try:
        with open(csv_path, newline='') as f:
            reader = csv.DictReader(f)
            if 'Filename' not in reader.fieldnames:
                raise ValueError("CSV must have a 'Filename' column.")
            for row in reader:
                filename = row['Filename'].strip()
                parts = filename.split("_", 1)
                if len(parts) == 2:
                    timestamps.add(parts[1].rsplit(".", 1)[0])
        return sorted(timestamps)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

def find_cam_folders(rec_dir):
    return [p for p in rec_dir.iterdir() if p.is_dir() and p.name.startswith("CAM")]

def transfer_files(timestamps, cam_folders, dest_dir, dry_run=False):
    log = []
    missing = defaultdict(list)

    for cam_folder in cam_folders:
        cam_name = cam_folder.name
        dest_cam_folder = dest_dir / cam_name
        if not dry_run:
            dest_cam_folder.mkdir(parents=True, exist_ok=True)

        for ts in timestamps:
            found = False
            for ext in [".ts", ".mp4"]:
                filename = f"{cam_name}_{ts}{ext}"
                src_file = cam_folder / filename
                dest_file = dest_cam_folder / filename

                if src_file.exists():
                    action = "Would copy" if dry_run else "Copied"
                    log.append((cam_name, ts, filename, action))
                    if not dry_run:
                        try:
                            shutil.copy2(str(src_file), dest_file)
                            print(f"[{action}] {filename}")
                        except Exception as e:
                            print(f"[ERROR] {filename}: {e}")
                            log.append((cam_name, ts, filename, f"Error: {e}"))
                    found = True
                    break
            if not found:
                missing[cam_name].append(ts)

    return log, missing

def save_log(log, missing, dest_dir, dry_run=False):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    log_name = f"{'dry_run' if dry_run else 'file_transfer'}_log_{timestamp}.csv"
    log_path = dest_dir / log_name

    with open(log_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Camera", "Timestamp", "Filename", "Action"])
        writer.writerows(log)

        f.write("\n\nSummary\n")
        total_files = len(log)
        f.write(f"Timestamps processed: {len(set(ts for _, ts, _, _ in log))}\n")
        f.write(f"Total files handled: {total_files}\n")
        f.write(f"Dry run: {dry_run}\n")

        f.write("\nMissing Files by Camera:\n")
        for cam in sorted(missing):
            f.write(f"{cam}: {len(missing[cam])} missing\n")
            for ts in missing[cam]:
                f.write(f"  - {ts}\n")

    print(f"\nLog saved to: {log_path}")
    return log_path

def summarize_log(log, timestamps, cam_folders, missing):
    found = defaultdict(int)
    total_expected = len(timestamps) * len(cam_folders)
    for cam, _, _, action in log:
        if not action.startswith("Error") and "Would" not in action:
            found[cam] += 1
    summary = [
        f"\nSummary:",
        f"  Timestamps processed: {len(timestamps)}",
        f"  Expected total files: {total_expected}",
        f"  Total files handled:  {len(log)}",
    ]
    for cam in sorted(found):
        summary.append(f"  {cam}: {found[cam]} file(s)")
    for cam in sorted(missing):
        summary.append(f"  {cam}: {len(missing[cam])} file(s) MISSING")

    print("\n".join(summary))
    return summary

def ask_yes_no(question):
    while True:
        answer = input(f"{question} (y/n): ").strip().lower()
        if answer in ["y", "n"]:
            return answer == "y"

def load_last_paths():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                lines = [line.strip() for line in f.readlines()]
                if len(lines) == 3:
                    return Path(lines[0]), Path(lines[1]), Path(lines[2])
        except:
            pass
    return None, None, None

def save_last_paths(csv, rec, dest):
    with open(CONFIG_FILE, "w") as f:
        f.write(f"{csv}\n{rec}\n{dest}\n")

def main():
    root = Tk()
    root.withdraw()

    last_csv, last_rec, last_dest = load_last_paths()

    # Select a valid CSV (retries until successful)
    while True:
        print("Select the CSV file with timestamps...")
        csv_path = Path(filedialog.askopenfilename(initialdir=last_csv if last_csv else None, filetypes=[("CSV Files", "*.csv")]))
        if not csv_path.exists():
            print("No CSV selected. Try again.")
            continue
        timestamps = extract_timestamps(csv_path)
        if timestamps is not None:
            break
        print("Invalid CSV format. Please select one with a 'Filename' column.")

    # Select a valid REC folder with CAMX folders
    while True:
        print("Select the root REC folder (must contain CAM1, CAM2, etc.)")
        rec_dir = Path(filedialog.askdirectory(initialdir=last_rec if last_rec else None, title="Select REC root directory"))
        if not rec_dir.exists():
            print("No REC folder selected. Try again.")
            continue

        cam_folders = find_cam_folders(rec_dir)
        if not cam_folders:
            print(f"Selected folder '{rec_dir}' does not contain any CAM folders. Try again.")
            continue

        break

    # Select destination folder
    while True:
        print("Select destination folder for copied files...")
        dest_dir = Path(filedialog.askdirectory(initialdir=last_dest if last_dest else None, title="Select output folder"))
        if not dest_dir.exists():
            print("No destination selected. Try again.")
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)

        if (dest_dir / "REC").exists():
            confirm = ask_yes_no("Warning: Destination contains a REC folder. Continue anyway?")
            if not confirm:
                continue
        break

    dry_run = ask_yes_no("Do a dry run? (Just list what would be copied)")

    save_last_paths(csv_path, rec_dir, dest_dir)

    print(f"\nProcessing {len(timestamps)} timestamps across {len(cam_folders)} camera folders...\n")
    log, missing = transfer_files(timestamps, cam_folders, dest_dir, dry_run)
    log_path = save_log(log, missing, dest_dir, dry_run)
    summarize_log(log, timestamps, cam_folders, missing)

    print("\nDone. Full log with summary and missing files saved.")
    print(f"Log path: {log_path}")

if __name__ == "__main__":
    main()
