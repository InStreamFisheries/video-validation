import vlc
import os
import re
import tkinter as tk
from tkinter import ttk, Label

players = []
frames = []  # to store frames for each player
updating_seek_bar = False
icon_path = None

def update_seek_bar():
    global updating_seek_bar
    if players and seek_bar:
        current_time_ms = players[0].get_time()
        duration_ms = players[0].get_length()

        if duration_ms > 0:
            updating_seek_bar = True  # block input during sys update
            seek_bar.set((current_time_ms / duration_ms) * 100)
            updating_seek_bar = False

    root.after(250, update_seek_bar)

def on_seek(value):
    global updating_seek_bar
    if not updating_seek_bar and players:
        duration_ms = players[0].get_length()
        if duration_ms > 0:
            seek_time_ms = int((float(value) / 100) * duration_ms)
            for player in players:
                player.set_time(seek_time_ms)

# initialize VLC instances for the given camera video files
def initialize_players(files):
    global players
    instances = [vlc.Instance("--file-caching=1000", "--network-caching=1000", "--avcodec-hw=dxva2") for _ in files]
    players = []

    for idx, (instance, file) in enumerate(zip(instances, files)):
        player = instance.media_player_new()
        media = instance.media_new(file)
        player.set_media(media)

        frame = frames[idx]
        player.set_hwnd(frame.winfo_id())

        player.play()
        players.append(player)

def start_playback():
    for player in players:
        player.play()

def toggle_play_pause():
    for player in players:
        if player.is_playing():
            player.pause()
        else:
            player.play()

def stop():
    for player in players:
        player.stop()
    if root:
        root.destroy()

def change_speed(rate):
    for player in players:
        player.set_rate(rate)

def rewind_1_4_sec():
    for player in players:
        player.set_time(max(player.get_time() - 250, 0))

def progress_1_4_sec():
    for player in players:
        player.set_time(max(player.get_time() + 250, 0))

def rewind_30s():
    for player in players:
        player.set_time(max(player.get_time() - 30000, 0))

def progress_30s():
    for player in players:
        player.set_time(player.get_time() + 30000)

# update timer display for all players
def update_timer():
    if players:
        current_time_ms = sum(player.get_time() for player in players) // len(players)
        current_time_sec = current_time_ms // 1000
        minutes, seconds = divmod(current_time_sec, 60)
        duration_ms = players[0].get_length()
        duration_sec = duration_ms // 1000
        duration_minutes, duration_seconds = divmod(duration_sec, 60)

        timer_label.config(text=f"{minutes:02}:{seconds:02} / {duration_minutes:02}:{duration_seconds:02}")

        if hasattr(root, "footage_start_time"):
            total_seconds = root.footage_start_time + current_time_sec
            hr, rem = divmod(total_seconds, 3600)
            mn, sc = divmod(rem, 60)
            overlay_label.config(text=f"Footage Time: {hr:02}:{mn:02}:{sc:02}")

    root.after(1000, update_timer)

def on_closing():
    for player in players:
        player.stop()
    if root:
        root.destroy()
        root.quit()

def on_key_press(event):
    if event.keysym == "Return":
        toggle_play_pause()

# GUI setup
def create_gui(files):
    global root, frames, now_playing_label, timer_label, seek_bar, overlay_label
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.title("Video Playback")
    root.bind("<Return>", on_key_press)

    if icon_path:
        try:
            root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Failed to load icon in video player: {e}. Using default icon.")
    else:
        print("Icon path not set in video player.")

    num_videos = len(files)
    cols = int(num_videos**0.5 + 0.5)
    rows = (num_videos + cols - 1) // cols

    for r in range(rows + 1):
        root.grid_rowconfigure(r, weight=1)
    for c in range(cols):
        root.grid_columnconfigure(c, weight=1)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight() - 80  # leave space for taskbar
    video_height = int(screen_height * 0.8 / rows)
    # create frames for each video and the controls
    frames = []
    for idx in range(num_videos):
        row, col = divmod(idx, cols)
        frame = tk.Frame(root, width=screen_width//cols, height=video_height)
        frame.grid(row=row, column=col, sticky="nsew")
        frame.grid_propagate(False)
        frames.append(frame)

    control_frame = tk.Frame(root)
    control_frame.grid(row=rows, column=0, columnspan=cols, sticky="nsew")

    initialize_players(files)

    play_pause_button = ttk.Button(control_frame, text="Play/Pause", command=toggle_play_pause)
    play_pause_button.grid(row=0, column=1, padx=5, pady=5)
    stop_button = ttk.Button(control_frame, text="Stop", command=stop)
    stop_button.grid(row=0, column=2, padx=5, pady=5)

    speed_label = ttk.Label(control_frame, text="Speed:")
    speed_label.grid(row=1, column=0, padx=5, pady=5)

    for i, rate in enumerate([0.25, 0.5, 1, 2, 4]):
        speed_button = ttk.Button(control_frame, text=f"{rate}x", command=lambda r=rate: change_speed(r))
        speed_button.grid(row=1, column=i + 1, padx=5, pady=5)

    rewind_1_4_button = ttk.Button(control_frame, text="Rewind (1/4s)", command=rewind_1_4_sec)
    rewind_1_4_button.grid(row=3, column=0, padx=5, pady=5)
    progress_1_4_button = ttk.Button(control_frame, text="Progress (1/4s)", command=progress_1_4_sec)
    progress_1_4_button.grid(row=3, column=1, padx=5, pady=5)

    rewind_30_button = ttk.Button(control_frame, text="Rewind (30s)", command=rewind_30s)
    rewind_30_button.grid(row=3, column=2, padx=5, pady=5)
    progress_30_button = ttk.Button(control_frame, text="Progress (30s)", command=progress_30s)
    progress_30_button.grid(row=3, column=3, padx=5, pady=5)

    timer_label = ttk.Label(control_frame, text="00:00 / 00:00")
    timer_label.grid(row=4, column=1, padx=5, pady=5, columnspan=2)
    # can change this based on people's needs. Seems some projects don't want 4x, want more granular speed changes? to add speeds just add ",x"
    filename = os.path.basename(files[0])
    display_name = filename[5:] if filename.startswith("CAM") else filename

    parts = filename.split("_")
    if len(parts) >= 3:
        time_part = parts[2][:6]  # HHMMSS
        try:
            h, m, s = int(time_part[0:2]), int(time_part[2:4]), int(time_part[4:6])
            root.footage_start_time = h * 3600 + m * 60 + s
        except:
            root.footage_start_time = 0
    else:
        root.footage_start_time = 0

    now_playing_label = ttk.Label(control_frame, text=f"Now playing: {display_name}")
    now_playing_label.grid(row=6, column=0, padx=5, pady=5, columnspan=3)

    seek_bar = ttk.Scale(
        control_frame,
        from_=0,
        to=100,
        orient="horizontal",
        command=on_seek
    )
    seek_bar.grid(row=5, column=1, padx=5, pady=5, columnspan=3, sticky="ew")

    overlay_label = ttk.Label(control_frame, text="Footage Time: --:--:--", font=("TkDefaultFont", 10, "bold"))
    overlay_label.grid(row=7, column=0, padx=5, pady=5, columnspan=3, sticky="ew")

    update_timer()
    update_seek_bar()
    root.mainloop()

def play_videos(vlc_path, files):
    create_gui(files)