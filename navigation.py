import os
import re
import threading
import logging
from collections import defaultdict
from tkinter import Tk, filedialog, StringVar, Label, Button, Frame, Toplevel, messagebox, ttk
import tkinter as tk
import json
from video_player import play_videos
import sys

def get_writable_path(filename):
    if getattr(sys, 'frozen', False):
        app_name = "Video Validation"
        appdata_dir = os.getenv('APPDATA')
        if appdata_dir:
            app_folder = os.path.join(appdata_dir, app_name)
            os.makedirs(app_folder, exist_ok=True)
            return os.path.join(app_folder, filename)
        else:
            return os.path.join(os.path.dirname(sys.executable), filename)
    else:
        return os.path.join(os.path.dirname(__file__), filename)

logger = logging.getLogger(__name__)
logger.debug("navigation.py initialized.")

#adding mkv support
file_pattern = re.compile(r"^(CAM\d+)_((\d{8})_(\d{6}|\d{4}))\.(mp4|ts|mkv)$")
camera_files = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
icon_path = None

config = {
    "vlc_path": None,
    "rec_path": None,
}

CONFIG_FILE = get_writable_path("config.json")

config_data = {
    "last_drive": None,
    "viewed_files": {},
    "last_viewed_file": None
}

viewed_times = set()

def load_config():
    global config_data, viewed_times
    logger.info(f"Using config.json at: {CONFIG_FILE}")
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config_data = json.load(f)
                viewed_times = set(config_data.get("viewed_files", {}).keys())
                logger.info(f"Loaded {len(viewed_times)} viewed times. Last drive: {config_data.get('last_drive')}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")

def save_config():
    global config_data
    config_data["viewed_files"] = {k: True for k in viewed_times}
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=2)
            logger.info(f"Saved config with {len(viewed_times)} viewed times and last drive: {config_data.get('last_drive')}")
    except Exception as e:
        logger.error(f"Error saving config: {e}")

def setup_vlc_path():
    try:
        import vlc
        vlc.Instance()
        config["vlc_path"] = ""
        return ""
    except Exception:
        pass
    if config["vlc_path"]:
        return config["vlc_path"]

    default_vlc_path = r"C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"
    if os.path.exists(default_vlc_path):
        config["vlc_path"] = default_vlc_path
        return default_vlc_path

    root = Tk()
    root.withdraw()
    vlc_path = filedialog.askopenfilename(
        title="Select VLC Executable (vlc.exe or cvlc)",
        filetypes=[("VLC Executable", "vlc.exe cvlc")]
    )
    if vlc_path and os.path.exists(vlc_path):
        config["vlc_path"] = vlc_path
        return vlc_path
    else:
        logger.error("VLC path not selected. Exiting.")
        exit()

def load_camera_files():
    global camera_files
    rec_path = filedialog.askdirectory(title="Select the REC Folder")
    if not rec_path:
        logger.warning("No directory selected.")
        return False

    config["rec_path"] = rec_path
    config_data["last_drive"] = rec_path
    save_config()

    logger.info(f"Selected REC path: {rec_path}")
    return parse_existing_camera_files()

def parse_existing_camera_files():
    global camera_files
    rec_path = config["rec_path"]
    if not rec_path or not os.path.exists(rec_path):
        logger.warning("Invalid REC path in config.")
        return False

    logger.info(f"Re-loading existing REC path: {rec_path}")
    camera_files.clear()

    for cam_num in range(1, 11):
        cam_folder = os.path.join(rec_path, f"CAM{cam_num}")
        logger.debug(f"Scanning folder: {cam_folder}")

        if os.path.exists(cam_folder):
            for file in os.listdir(cam_folder):
                full_path = os.path.join(cam_folder, file)
                if os.path.isdir(full_path):
                    logger.debug(f"Skipping directory: {file}")
                    continue
                if not file.lower().endswith((".mp4", ".ts", ".mkv")):
                    logger.debug(f"Skipping non-video file: {file}")
                    continue
                match = file_pattern.match(file)
                if match:
                    cam_id, timestamp, date_part, time_part, _ = match.groups()
                    year, month, day = date_part[:4], date_part[4:6], date_part[6:8]
                    camera_files[year][month][day].setdefault(time_part, []).append(full_path)
                else:
                    logger.debug(f"Unmatched file: {file}")
        else:
            logger.warning(f"Camera folder does not exist: {cam_folder}")

    total_files = sum(len(times) for year in camera_files.values()
                      for month in year.values()
                      for day in month.values()
                      for times in day.values())
    logger.info(f"Camera files loaded: {total_files}")
    return bool(camera_files)

def display_summary():
    unique_cameras = set()
    total_timestamps = 0
    total_size_gb = 0

    for year in camera_files:
        for month in camera_files[year]:
            for day in camera_files[year][month]:
                for time in camera_files[year][month][day]:
                    files = camera_files[year][month][day][time]
                    unique_cameras.update(os.path.basename(file).split('_')[0] for file in files)

    cam1_folder = os.path.join(config["rec_path"], "CAM1")
    if os.path.exists(cam1_folder):
        for file in os.listdir(cam1_folder):
            if file.lower().endswith((".mp4", ".ts")) and not os.path.isdir(os.path.join(cam1_folder, file)):
                total_timestamps += 1

    for cam_num in range(1, 11):
        cam_folder = os.path.join(config["rec_path"], f"CAM{cam_num}")
        if os.path.exists(cam_folder):
            for file in os.listdir(cam_folder):
                full_path = os.path.join(cam_folder, file)
                if file.lower().endswith((".mp4", ".ts")) and not os.path.isdir(full_path):
                    total_size_gb += os.path.getsize(full_path)

        corrupted_folder = os.path.join(cam_folder, "corrupted")
        if os.path.exists(corrupted_folder):
            for file in os.listdir(corrupted_folder):
                full_path = os.path.join(corrupted_folder, file)
                if file.lower().endswith((".mp4", ".ts")) and not os.path.isdir(full_path):
                    total_size_gb += os.path.getsize(full_path)

    total_size_gb /= (1024 ** 3)
    return len(unique_cameras), total_timestamps, total_size_gb

def show_navigation_ui():
    root = Tk()
    load_config()
    root.title("Video Navigation")
    root.geometry("300x330")
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=0)
    root.grid_columnconfigure(2, weight=1)

    if icon_path:
        try:
            root.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"Failed to load icon: {e}")

    year_var = StringVar()
    month_var = StringVar()
    day_var = StringVar()
    time_var = StringVar()

    rec_path_label = Label(root, text=f"Selected Drive: {config.get('rec_path', 'No Drive Selected')}", anchor="w", wraplength=400)
    rec_path_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="w")

    drive_button = Button(root, text="Select Drive", command=lambda: threading.Thread(target=lambda: threaded_load(force_select=True)).start())
    drive_button.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 15), sticky="ew")

    stats = {
        "cameras": Label(root, text="Total cameras found:\n0", anchor="w", justify="left"),
        "timestamps": Label(root, text="Total timestamps:\n0", anchor="w", justify="left"),
        "footage": Label(root, text="Total footage:\n0.00 GB", anchor="w", justify="left")
    }

    for i, key in enumerate(stats):
        stats[key].grid(row=i + 2, column=0, padx=10, pady=2, sticky="w")

    dropdowns = []
    labels = ["Year", "Month", "Day", "Time"]
    vars_ = [year_var, month_var, day_var, time_var]

    for i, label in enumerate(labels):
        frame = Frame(root)
        frame.grid(row=i + 2, column=2, sticky="e", padx=(0, 10), pady=2)
        lbl = Label(frame, text=f"{label}:", anchor="e")
        lbl.pack(side="left", padx=(0, 4))
        cb = ttk.Combobox(frame, textvariable=vars_[i], state="readonly", width=14)
        cb.pack(side="left")
        dropdowns.append(cb)

    def update_summary():
        c, t, g = display_summary()
        stats["cameras"].config(text=f"Total cameras found:\n{c}")
        stats["timestamps"].config(text=f"Total timestamps:\n{t}")
        stats["footage"].config(text=f"Total footage:\n{g:.2f} GB")

    def update_years():
        years = sorted(camera_files.keys())
        dropdowns[0]['values'] = years
        if years:
            year_var.set(years[0])
            update_months()

    def update_months(*args):
        y = year_var.get()
        months = sorted(camera_files.get(y, {}).keys())
        dropdowns[1]['values'] = months
        if months:
            month_var.set(months[0])
            update_days()

    def update_days(*args):
        y, m = year_var.get(), month_var.get()
        days = sorted(camera_files.get(y, {}).get(m, {}).keys())
        dropdowns[2]['values'] = days
        if days:
            day_var.set(days[0])
            update_times()

    def update_times(*args):
        y, m, d = year_var.get(), month_var.get(), day_var.get()
        raw_to_formatted = {}
        formatted_times = []

        times = sorted(camera_files.get(y, {}).get(m, {}).get(d, {}).keys())
        for raw in times:
            if len(raw) == 6:
                formatted = f"{raw[:2]}:{raw[2:4]}:{raw[4:]}"
            elif len(raw) == 4:
                formatted = f"{raw[:2]}:{raw[2:]}:00"
            else:
                formatted = "00:00:00"

            viewed_key = f"{y}/{m}/{d}/{raw}"
            if viewed_key in viewed_times:
                display_text = f"✔️ {formatted}"
            else:
                display_text = f"   {formatted}"

            raw_to_formatted[display_text] = raw
            formatted_times.append(display_text)

        dropdowns[3]['values'] = formatted_times
        if formatted_times:
            last_viewed = config_data.get("last_viewed_file")
            for display_text, raw in raw_to_formatted.items():
                viewed_key = f"{y}/{m}/{d}/{raw}"
                if viewed_key == last_viewed:
                    time_var.set(display_text)
                    setattr(time_var, "raw_time", raw)
                    break
            else:
                time_var.set(formatted_times[0])
                setattr(time_var, "raw_time", raw_to_formatted[formatted_times[0]])

        def on_select(event):
            selected_display_text = time_var.get()
            raw = raw_to_formatted.get(selected_display_text)
            if raw:
                setattr(time_var, "raw_time", raw)

        dropdowns[3].bind("<<ComboboxSelected>>", on_select)
    dropdowns[0].bind("<<ComboboxSelected>>", update_months)
    dropdowns[1].bind("<<ComboboxSelected>>", update_days)
    dropdowns[2].bind("<<ComboboxSelected>>", update_times)

    def threaded_load(force_select=False):
        loading = Toplevel(root)
        Label(loading, text="Scanning drive, please wait...").pack(padx=20, pady=20)
        root.update_idletasks()
        x, y = root.winfo_x(), root.winfo_y()
        w, h = root.winfo_width(), root.winfo_height()
        loading.geometry(f"250x80+{x + w//2 - 125}+{y + h//2 - 40}")
        loading.transient(root)
        loading.grab_set()
        loading.update()

        def bg():
            if force_select or not config.get("rec_path"):
                success = load_camera_files()
            else:
                success = parse_existing_camera_files()

            if success:
                rec_path_label.config(text=f"Selected Drive: {config['rec_path']}")
                update_years()
                update_summary()
            loading.destroy()

        threading.Thread(target=bg).start()

    def clear_viewed_times():
        confirm = messagebox.askyesno("Confirm Clear", "Are you sure you want to clear all viewed times?")
        if confirm:
            viewed_times.clear()
            config_data["viewed_files"] = {}
            config_data["last_viewed_file"] = None
            save_config()
            update_times()
            logger.info("Viewed times cleared.")

    def play_selected_videos():
        vlc = setup_vlc_path()
        y, m, d = year_var.get(), month_var.get(), day_var.get()
        t = getattr(time_var, "raw_time", None)
        if y and m and d and t:
            try:
                viewed_key = f"{y}/{m}/{d}/{t}"
                viewed_times.add(viewed_key)
                config_data["last_viewed_file"] = viewed_key
                save_config()

                logger.info(f"Playing video(s) for: {viewed_key}")

                play_videos(vlc, camera_files[y][m][d][t], icon_path)
                update_times()

            except KeyError:
                logger.error("Selected time not found.")

    Button(root, text="Play Selected", command=play_selected_videos).grid(
        row=6, column=0, columnspan=3, padx=10, pady=20, sticky="ew"
    )

    #Button(root, text="Clear Viewed Times", command=clear_viewed_times).grid(
    #row=7, column=0, columnspan=3, padx=10, pady=(0, 20), sticky="ew"
    #)

    if config_data.get("last_drive"):
        config["rec_path"] = config_data["last_drive"]
        threading.Thread(target=lambda: threaded_load(force_select=False)).start()

    root.mainloop()