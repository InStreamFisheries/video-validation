import os
import re
from collections import defaultdict
from tkinter import Tk, filedialog, StringVar, Label, Button, OptionMenu
from video_player import play_videos

# match the file naming pattern
file_pattern = re.compile(r"^(CAM\d+)_(\d{8}_\d{4})\.mp4$")
camera_files = defaultdict(lambda: defaultdict(lambda: defaultdict(dict))) 

config = {
    "vlc_path": None,
    "rec_path": None,
}

def setup_vlc_path():
    """Retrieve or set up the VLC path."""
    if config["vlc_path"]:
        return config["vlc_path"]

    default_vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
    if os.path.exists(default_vlc_path):
        config["vlc_path"] = default_vlc_path
        return default_vlc_path

    # prompt user for VLC path
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

# load files and categorize by timestamp
def load_camera_files():
    global camera_files
    rec_path = filedialog.askdirectory(title="Select the REC Folder")
    if not rec_path:
        print("No directory selected.")
        return False 

    config["rec_path"] = rec_path 
    camera_files.clear() 

    for cam_num in range(1, 11):
        cam_folder = os.path.join(rec_path, f"CAM{cam_num}")
        if os.path.exists(cam_folder):
            for file in os.listdir(cam_folder):
                match = file_pattern.match(file)
                if match:
                    cam_id, timestamp = match.groups()
                    year, month, day, time = timestamp[:4], timestamp[4:6], timestamp[6:8], timestamp[8:]
                    if time not in camera_files[year][month][day]:
                        camera_files[year][month][day][time] = []
                    file_path = os.path.join(cam_folder, file)
                    camera_files[year][month][day][time].append(file_path)

    return bool(camera_files)

def get_saved_rec_path():
    return config.get("rec_path")

# display a summary of available footage
# only works in terminal
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
                    total_timestamps += 1
                    total_size_gb += sum(os.path.getsize(file) for file in files)

    total_size_gb /= (1024 ** 3)
    print(f"\nSummary of Available Footage:")
    print(f"Total cameras found: {len(unique_cameras)}")
    print(f"Total timestamp chunks found: {total_timestamps}")
    print(f"Total footage size: {total_size_gb:.2f} GB\n")

def show_navigation_ui():
    root = Tk()
    root.title("Video Navigation")
    root.geometry("600x400")  # testing size

    # selection variables for dropdowns
    year_var = StringVar(root)
    month_var = StringVar(root)
    day_var = StringVar(root)
    time_var = StringVar(root)

    # load saved REC path if available
    saved_rec_path = get_saved_rec_path()
    if saved_rec_path:
        rec_path_label_text = f"Selected Drive: {saved_rec_path}"
    else:
        rec_path_label_text = "No Drive Selected"

    # drive path label to display selected or saved drive path
    drive_path_label = Label(root, text=rec_path_label_text, wraplength=400, anchor="w")
    drive_path_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")

    def select_drive():
        """Select drive and load camera files."""
        if load_camera_files():
            drive_path_label.config(text=f"Selected Drive: {config['rec_path']}")
            display_summary()
            update_years()

    def update_years():
        """Populate the year dropdown based on loaded files."""
        year_options = sorted(camera_files.keys())
        year_var.set("Select Year")
        year_menu['menu'].delete(0, 'end')
        for year in year_options:
            year_menu['menu'].add_command(label=year, command=lambda value=year: year_var.set(value))
        update_months()

    def update_months(*args):
        """Update the months based on the selected year."""
        selected_year = year_var.get()
        month_var.set("Select Month")
        month_menu['menu'].delete(0, 'end')
        if selected_year in camera_files:
            for month in sorted(camera_files[selected_year].keys()):
                month_menu['menu'].add_command(label=month, command=lambda value=month: month_var.set(value))
        update_days()

    def update_days(*args):
        """Update the days based on the selected month."""
        selected_year = year_var.get()
        selected_month = month_var.get()
        day_var.set("Select Day")
        day_menu['menu'].delete(0, 'end')
        if selected_month in camera_files[selected_year]:
            for day in sorted(camera_files[selected_year][selected_month].keys()):
                day_menu['menu'].add_command(label=day, command=lambda value=day: day_var.set(value))
        update_times()

    def update_times(*args):
        """Update the times based on the selected day."""
        selected_year = year_var.get()
        selected_month = month_var.get()
        selected_day = day_var.get()
        time_var.set("Select Time")
        time_menu['menu'].delete(0, 'end')
    
        if selected_day in camera_files[selected_year][selected_month]:
            for time in sorted(camera_files[selected_year][selected_month][selected_day].keys()):
                formatted_time = f"{time[1:3]}:{time[3:]}" if time.startswith("_") else f"{time[:2]}:{time[2:]}"
                time_menu['menu'].add_command(
                    label=formatted_time, 
                    command=lambda value=time: time_var.set(value)
                )

    year_var.trace("w", update_months)
    month_var.trace("w", update_days)
    day_var.trace("w", update_times)

    # dropdown menus and Labels
    Label(root, text="Year:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
    year_menu = OptionMenu(root, year_var, "Select Year")
    year_menu.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

    Label(root, text="Month:").grid(row=3, column=0, padx=10, pady=10, sticky="e")
    month_menu = OptionMenu(root, month_var, "Select Month")
    month_menu.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

    Label(root, text="Day:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
    day_menu = OptionMenu(root, day_var, "Select Day")
    day_menu.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

    Label(root, text="Time:").grid(row=5, column=0, padx=10, pady=10, sticky="e")
    time_menu = OptionMenu(root, time_var, "Select Time")
    time_menu.grid(row=5, column=1, padx=10, pady=10, sticky="ew")

    drive_button = Button(root, text="Select Drive", command=select_drive)
    drive_button.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

    def play_selected_videos():
        vlc_path = setup_vlc_path()
        selected_year = year_var.get()
        selected_month = month_var.get()
        selected_day = day_var.get()
        selected_time = time_var.get().replace(":", "")
    
        if selected_year and selected_month and selected_day and selected_time:
            try:
                print(f"\nPlaying videos for timestamp: {selected_year}-{selected_month}-{selected_day}_{selected_time}")
                play_videos(vlc_path, camera_files[selected_year][selected_month][selected_day][selected_time])
            except KeyError:
                print("Error: Selected time not found.")

    play_button = Button(root, text="Play Selected", command=play_selected_videos)
    play_button.grid(row=6, column=0, columnspan=2, pady=20, sticky="ew")

    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    root.mainloop()
