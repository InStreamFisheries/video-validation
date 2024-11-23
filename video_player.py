import vlc
import os
import tkinter as tk
from tkinter import ttk, Label

players = []
frames = []  # to store frames for each player
updating_seek_bar = False

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
def initialize_players(files, screen_width, screen_height):
    global players
    instances = [vlc.Instance("--file-caching=1000", "--network-caching=1000") for _ in files]
    players = []

    for idx, (instance, file) in enumerate(zip(instances, files)):
        player = instance.media_player_new()
        media = instance.media_new(file)
        player.set_media(media)

        frame = frames[idx]  # attach player to specific tkinter frame
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
    """Stop all videos and close the Tkinter root window."""
    for player in players:
        player.stop()
    if root:
        root.destroy()

def change_speed(rate):
    for player in players:
        player.set_rate(rate)
def rewind_1_4_sec():
    for player in players:
        player.set_time(max(player.get_time() - 250, 0))  # 1/4 second
def progress_1_4_sec():
    for player in players:
        player.set_time(max(player.get_time() + 250, 0))  # 1/4 second
def rewind_30s():
    for player in players:
        player.set_time(max(player.get_time() - 30000, 0))  # 30 seconds
def progress_30s():
    for player in players:
        player.set_time(player.get_time() + 30000)  # 30 seconds

# seek to a specific time across all videos
def seek_to_time():
    time_str = timer_entry.get()
    try:
        minutes, seconds = map(int, time_str.split(":"))
        target_time_ms = (minutes * 60 + seconds) * 1000
        for player in players:
            player.set_time(target_time_ms)
    except ValueError:
        print("Invalid time format. Use mm:ss.")

# update timer display for all players
def update_timer():
    if players:
        current_time_ms = sum(player.get_time() for player in players) // len(players)
        current_time_sec = current_time_ms // 1000
        minutes, seconds = divmod(current_time_sec, 60)
        
        timer_entry.delete(0, tk.END)
        timer_entry.insert(0, f"{minutes:02}:{seconds:02}")
        
    root.after(1000, update_timer)

def on_closing():
    for player in players:
        player.stop()
    root.destroy()

# gui setup
def create_gui(files):
    global root, frames, now_playing_label, timer_entry, seek_bar
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", stop)
    root.title("Video Playback")

    icon_path = os.path.join(os.path.dirname(__file__), "appIcon.ico")
    try:
        root.iconbitmap(icon_path)
    except Exception as e:
        print(f"Failed to load icon: {e}. Using default icon.")

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # create frames for each video and the controls
    frames = [tk.Frame(root, width=screen_width//2, height=screen_height//2) for _ in range(3)]
    for idx, frame in enumerate(frames):
        row, col = divmod(idx, 2)
        frame.grid(row=row, column=col, sticky="nsew")
        frame.grid_propagate(False)

    # frame in bottom-right
    control_frame = tk.Frame(root, width=screen_width//2, height=screen_height//2)
    control_frame.grid(row=1, column=1, sticky="nsew")
    control_frame.grid_propagate(False)

    initialize_players(files, screen_width, screen_height)

    play_pause_button = ttk.Button(control_frame, text="Play/Pause", command=toggle_play_pause)
    play_pause_button.grid(row=0, column=0, padx=5, pady=5)

    stop_button = ttk.Button(control_frame, text="Stop", command=stop)
    stop_button.grid(row=0, column=1, padx=5, pady=5)

    speed_label = ttk.Label(control_frame, text="Speed:")
    speed_label.grid(row=1, column=0, padx=5, pady=5)
    for i, rate in enumerate([1, 2, 4]):
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

    timer_entry = ttk.Entry(control_frame, width=10)
    timer_entry.grid(row=4, column=0, padx=5, pady=5, columnspan=2)
    timer_entry.insert(0, "00:00")

    seek_button = ttk.Button(control_frame, text="Seek", command=seek_to_time)
    seek_button.grid(row=4, column=2, padx=5, pady=5)

    # display "Now Playing" label
        # get and format the filename of the first video file
    filename = os.path.basename(files[0])
    display_name = filename[5:] if filename.startswith("CAM") else filename
        # display "Now Playing" label with the formatted filename
    now_playing_label = ttk.Label(control_frame, text=f"Now playing: {display_name}")
    now_playing_label.grid(row=6, column=0, padx=5, pady=5, columnspan=3)

    update_timer()

    seek_bar = ttk.Scale(
        control_frame,
        from_=0,
        to=100,
        orient="horizontal",
        command=on_seek
    )
    seek_bar.grid(row=5, column=0, padx=5, pady=5, columnspan=3, sticky="ew")
    root.protocol("WM_DELETE_WINDOW", on_closing)
    update_seek_bar()
    root.mainloop()

def play_videos(vlc_path, files):
    create_gui(files)