import os
import re
from collections import defaultdict
from tkinter import Tk, filedialog, StringVar, Label, Button, OptionMenu, Frame
from video_player import play_videos

file_pattern = re.compile(r"^(CAM\d+)_((\d{8})_(\d{6}|\d{4}))\.(mp4|ts)$")
camera_files = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
icon_path = None

config = {
    "vlc_path": None,
    "rec_path": None,
}

def setup_vlc_path():
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
        print("VLC path not selected. Exiting.")
        exit()

def load_camera_files():
    global camera_files
    rec_path = filedialog.askdirectory(title="Select the REC Folder")
    if not rec_path:
        print("No directory selected.")
        return False

    config["rec_path"] = rec_path
    print("Selected REC path:", rec_path)
    camera_files.clear()

    for cam_num in range(1, 11):
        cam_folder = os.path.join(rec_path, f"CAM{cam_num}")
        if os.path.exists(cam_folder):
            for file in os.listdir(cam_folder):
                if os.path.isdir(os.path.join(cam_folder, file)):
                    continue
                if not file.lower().endswith((".mp4", ".ts")):
                    continue
                match = file_pattern.match(file)
                if match:
                    cam_id, timestamp, date_part, time_part, _ = match.groups()
                    year, month, day = date_part[:4], date_part[4:6], date_part[6:8]
                    if time_part not in camera_files[year][month][day]:
                        camera_files[year][month][day][time_part] = []
                    file_path = os.path.join(cam_folder, file)
                    camera_files[year][month][day][time_part].append(file_path)

    print("Camera files found:", sum(len(times) for year in camera_files.values() for month in year.values() for day in month.values() for times in day.values()))
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
                if file.lower().endswith((".mp4", ".ts")) and not os.path.isdir(os.path.join(cam_folder, file)):
                    total_size_gb += os.path.getsize(os.path.join(cam_folder, file))

        corrupted_folder = os.path.join(cam_folder, "corrupted")
        if os.path.exists(corrupted_folder):
            for file in os.listdir(corrupted_folder):
                if file.lower().endswith((".mp4", ".ts")) and not os.path.isdir(os.path.join(corrupted_folder, file)):
                    total_size_gb += os.path.getsize(os.path.join(corrupted_folder, file))

    total_size_gb /= (1024 ** 3)
    return len(unique_cameras), total_timestamps, total_size_gb

def show_navigation_ui():
    root = Tk()
    root.title("Video Navigation")
    root.geometry("325x325")
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=0)
    root.grid_columnconfigure(2, weight=0)

    if icon_path:
        try:
            root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Failed to load icon in navigation: {e}. Using default icon.")
    else:
        print("Icon path not set in navigation.")

    year_var = StringVar(root, value="Select Year")
    month_var = StringVar(root, value="Select Month")
    day_var = StringVar(root, value="Select Day")
    time_var = StringVar(root, value="Select Time")

    rec_path_label_text = f"Selected Drive: {config.get('rec_path', 'No Drive Selected')}"
    drive_path_label = Label(root, text=rec_path_label_text, wraplength=300, anchor="w")
    drive_path_label.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="w")

    summary_label_cameras = Label(root, text="Total cameras found:\n0", anchor="w", justify="left")
    summary_label_timestamps = Label(root, text="Total timestamp chunks:\n0", anchor="w", justify="left")
    summary_label_size = Label(root, text="Total footage size:\n0.00 GB", anchor="w", justify="left")

    summary_label_cameras.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")
    summary_label_timestamps.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="w")
    summary_label_size.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="w")

    def update_summary():
        unique_cameras, total_timestamps, total_size_gb = display_summary()
        summary_label_cameras.config(text=f"Total cameras found:\n{unique_cameras}")
        summary_label_timestamps.config(text=f"Total timestamp chunks:\n{total_timestamps}")
        summary_label_size.config(text=f"Total footage size:\n{total_size_gb:.2f} GB")

    def select_drive():
        if load_camera_files():
            drive_path_label.config(text=f"Selected Drive: {config['rec_path']}")
            update_years()
            update_summary()

    def update_years():
        year_menu['menu'].delete(0, 'end')
        years = sorted(camera_files.keys())
        for year in years:
            year_menu['menu'].add_command(label=year, command=lambda value=year: year_var.set(value))
        update_months()

    def update_months(*args):
        month_menu['menu'].delete(0, 'end')
        selected_year = year_var.get()
        if selected_year in camera_files:
            months = sorted(camera_files[selected_year].keys())
            for month in months:
                month_menu['menu'].add_command(label=month, command=lambda value=month: month_var.set(value))
        update_days()

    def update_days(*args):
        day_menu['menu'].delete(0, 'end')
        selected_year = year_var.get()
        selected_month = month_var.get()
        if selected_year in camera_files and selected_month in camera_files[selected_year]:
            days = sorted(camera_files[selected_year][selected_month].keys())
            for day in days:
                day_menu['menu'].add_command(label=day, command=lambda value=day: day_var.set(value))
        update_times()

    def update_times(*args):
        time_menu['menu'].delete(0, 'end')
        selected_year = year_var.get()
        selected_month = month_var.get()
        selected_day = day_var.get()

        if selected_year in camera_files and selected_month in camera_files[selected_year] and selected_day in camera_files[selected_year][selected_month]:
            times = sorted(camera_files[selected_year][selected_month][selected_day].keys())
            for raw_time in times:
                if len(raw_time) == 6:
                    formatted_time = f"{raw_time[0:2]}:{raw_time[2:4]}:{raw_time[4:6]}"
                elif len(raw_time) == 4:
                    formatted_time = f"{raw_time[0:2]}:{raw_time[2:4]}:00"
                else:
                    formatted_time = "00:00:00"
                def callback(rt=raw_time, ft=formatted_time):
                    time_var.set(ft)
                    setattr(time_var, 'raw_time', rt)
                time_menu['menu'].add_command(label=formatted_time, command=callback)

    year_var.trace("w", update_months)
    month_var.trace("w", update_days)
    day_var.trace("w", update_times)

    Label(root, text="Year:").grid(row=2, column=1, sticky="e")
    year_menu = OptionMenu(root, year_var, "Select Year")
    year_menu.grid(row=2, column=2, padx=(5, 10), pady=2, sticky="e")
    year_menu.config(width=10)

    Label(root, text="Month:").grid(row=3, column=1, sticky="e")
    month_menu = OptionMenu(root, month_var, "Select Month")
    month_menu.grid(row=3, column=2, padx=(5, 10), pady=2, sticky="e")
    month_menu.config(width=10)

    Label(root, text="Day:").grid(row=4, column=1, sticky="e")
    day_menu = OptionMenu(root, day_var, "Select Day")
    day_menu.grid(row=4, column=2, padx=(5, 10), pady=2, sticky="e")
    day_menu.config(width=10)

    Label(root, text="Time:").grid(row=5, column=1, sticky="e")
    time_menu = OptionMenu(root, time_var, "Select Time")
    time_menu.grid(row=5, column=2, padx=(5, 10), pady=2, sticky="e")
    time_menu.config(width=10)

    drive_button = Button(root, text="Select Drive", command=select_drive)
    drive_button.grid(row=1, column=0, columnspan=3, padx=40, pady=10, sticky="ew")

    def play_selected_videos():
        vlc_path = setup_vlc_path()
        selected_year = year_var.get()
        selected_month = month_var.get()
        selected_day = day_var.get()
        selected_time = getattr(time_var, "raw_time", None)
        if selected_year and selected_month and selected_day and selected_time:
            try:
                play_videos(vlc_path, camera_files[selected_year][selected_month][selected_day][selected_time])
            except KeyError:
                print("Error: Selected time not found.")

    play_button = Button(root, text="Play Selected", command=play_selected_videos)
    play_button.grid(row=6, column=0, columnspan=3, padx=40, pady=10, sticky="ew")

    root.mainloop()