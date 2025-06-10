import vlc
import os
import tkinter as tk
from tkinter import ttk
import threading
import logging
import time
import atexit
import sys

# setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app_debug.log", mode='a'),
        logging.StreamHandler()
    ]
)

logging.debug("video_player.py initialized.")

if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    os.environ["PATH"] = f"{bundle_dir};{os.environ['PATH']}"
    os.environ["VLC_PLUGIN_PATH"] = os.path.join(bundle_dir, "plugins")
    logging.debug(f"PyInstaller detected. Using bundled VLC at: {bundle_dir}")

players = []
frames = []
icon_path = None
shutdown_called = False
last_files = []
last_known_rate = 1.0

pause_lock = threading.Lock()
pause_event = threading.Event()
pause_event.set()

sync_status_label = None

def cleanup_players():
    logging.debug("Cleanup: Stopping all VLC players")
    for idx, player in enumerate(players):
        try:
            player.stop()
            logging.debug(f"Player {idx+1} forcibly stopped during cleanup.")
        except Exception as e:
            logging.error(f"Error during cleanup for player {idx+1}: {e}")

atexit.register(cleanup_players)

def pause_all_players():
    with pause_lock:
        pause_event.clear()
        for idx, player in enumerate(players):
            try:
                player.pause()
                logging.debug(f"Player {idx+1} paused")
            except Exception as e:
                logging.error(f"Pause error on player {idx+1}: {e}")

def play_all_players():
    with pause_lock:
        for idx, player in enumerate(players):
            try:
                player.play()
                logging.debug(f"Player {idx+1} resumed")
            except Exception as e:
                logging.error(f"Play error on player {idx+1}: {e}")
        pause_event.set()

def jump_to_time():
    time_str = jump_entry.get()
    try:
        minutes, seconds = map(int, time_str.split(':'))
        jump_ms = (minutes * 60 + seconds) * 1000
        logging.debug(f"Jumping to {jump_ms} ms")
        pause_all_players()
        time.sleep(0.8)
        for idx, player in enumerate(players):
            player.set_time(jump_ms)
            logging.debug(f"Player {idx+1} jumped to {jump_ms} ms")
        time.sleep(1.2)
        pause_all_players()  # ensure players stay paused after jump
        logging.debug("All players paused after jump")
        if sync_status_label:
            sync_status_label.config(text="Synced to time: {:02}:{:02}".format(minutes, seconds), foreground="green")
    except Exception as e:
        logging.error(f"Invalid jump time input '{time_str}': {e}")
        if sync_status_label:
            sync_status_label.config(text="Invalid time format", foreground="red")

def toggle_play_pause():
    playing = any(player.is_playing() for player in players)
    if playing:
        pause_all_players()
    else:
        play_all_players()

def stop():
    for idx, player in enumerate(players):
        try:
            player.stop()
            logging.debug(f"Player {idx+1} stopped")
        except Exception as e:
            logging.error(f"Error stopping player {idx+1}: {e}")
    if root:
        root.quit()
        root.destroy()
        logging.debug("GUI closed")

def change_speed(rate):
    global last_known_rate
    last_known_rate = rate
    for idx, player in enumerate(players):
        try:
            player.set_rate(rate)
            logging.debug(f"Player {idx+1} speed set to {rate}x")
        except Exception as e:
            logging.error(f"Error changing speed on player {idx+1}: {e}")

def rewind_1_4_sec():
    for idx, player in enumerate(players):
        new_time = max(player.get_time() - 250, 0)
        player.set_time(new_time)
        logging.debug(f"Player {idx+1} rewinded 0.25s to {new_time} ms")

def progress_1_4_sec():
    for idx, player in enumerate(players):
        new_time = player.get_time() + 250
        player.set_time(new_time)
        logging.debug(f"Player {idx+1} forwarded 0.25s to {new_time} ms")

def rewind_30s():
    for idx, player in enumerate(players):
        new_time = max(player.get_time() - 30000, 0)
        player.set_time(new_time)
        logging.debug(f"Player {idx+1} rewinded 30s to {new_time} ms")

def progress_30s():
    for idx, player in enumerate(players):
        new_time = player.get_time() + 30000
        player.set_time(new_time)
        logging.debug(f"Player {idx+1} forwarded 30s to {new_time} ms")

def update_timer():
    if not hasattr(root, 'winfo_exists') or not root.winfo_exists():
        return
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
    global shutdown_called
    if shutdown_called:
        return
    shutdown_called = True
    logging.debug("Window close event triggered")
    cleanup_players()

    try:
        root.quit()
        logging.debug("Called root.quit()")
    except Exception as e:
        logging.error(f"Error in root.quit(): {e}")

    try:
        root.destroy()
        logging.debug("Called root.destroy()")
    except Exception as e:
        logging.error(f"Error in root.destroy(): {e}")

def on_key_press(event):
    if event.keysym == "Return":
        logging.debug("Return key pressed")
        toggle_play_pause()
    elif event.keysym == "F11":
        is_fullscreen = root.attributes("-fullscreen")
        root.attributes("-fullscreen", not is_fullscreen)
        logging.debug(f"Fullscreen toggled: now {'on' if not is_fullscreen else 'off'}")

def create_gui(files):
    global root, frames, jump_entry, timer_label, overlay_label, last_files, sync_status_label
    last_files = files[:]
    root = tk.Tk()
    logging.debug("Tkinter root window created.")
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.title("Video Playback")
    root.bind("<Return>", on_key_press)
    root.bind("<F11>", on_key_press)

    try:
        root.state('zoomed')
        logging.debug("Window state set to zoomed (maximized)")
    except Exception as e:
        logging.warning(f"Zoomed mode failed: {e}")

    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    root.lift()
    root.focus_force()

    num_videos = len(files)
    cols = int(num_videos ** 0.5 + 0.5)
    rows = (num_videos + cols - 1) // cols
    logging.debug(f"Layout: {rows} rows x {cols} cols for {num_videos} video(s)")

    for r in range(rows + 1):
        root.grid_rowconfigure(r, weight=1)
    for c in range(cols):
        root.grid_columnconfigure(c, weight=1)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight() - 80
    video_height = int(screen_height * 0.8 / rows)

    frames = []
    for idx in range(num_videos):
        row, col = divmod(idx, cols)
        frame = tk.Frame(root, width=screen_width // cols, height=video_height)
        frame.grid(row=row, column=col, sticky="nsew")
        frame.grid_propagate(False)
        frames.append(frame)

    control_frame = tk.Frame(root)
    control_frame.grid(row=rows, column=0, columnspan=cols, sticky="nsew")

    root.after(100, lambda: initialize_players(files))

    overlay_frames = []

    for idx, frame in enumerate(frames):
        frame.update_idletasks()
        x = frame.winfo_rootx() - root.winfo_rootx()
        y = frame.winfo_rooty() - root.winfo_rooty()
        w = frame.winfo_width()
        h = frame.winfo_height()

        # black box 40% width, 15% height in bottom right corner
        box_width = int(w * 0.40)
        box_height = int(h * 0.10)
        box_x = x + w - box_width - 10
        box_y = y + h - box_height - 10

        overlay = tk.Frame(root, bg="black")
        overlay.place(x=box_x, y=box_y, width=box_width, height=box_height)

        overlay_frames.append(overlay)

        def on_resize(event, overlay=overlay, frame=frame):
            frame.update_idletasks()
            x = frame.winfo_rootx() - root.winfo_rootx()
            y = frame.winfo_rooty() - root.winfo_rooty()
            w = frame.winfo_width()
            h = frame.winfo_height()
            box_width = int(w * 0.40)
            box_height = int(h * 0.10)
            box_x = x + w - box_width - 10
            box_y = y + h - box_height - 10
            overlay.place(x=box_x, y=box_y, width=box_width, height=box_height)

        frame.bind("<Configure>", on_resize)

    ttk.Button(control_frame, text="Play/Pause", command=toggle_play_pause).grid(row=0, column=1, padx=5, pady=5)
    ttk.Button(control_frame, text="Stop", command=stop).grid(row=0, column=2, padx=5, pady=5)

    ttk.Label(control_frame, text="Speed:").grid(row=1, column=0, padx=5, pady=5)
    for i, rate in enumerate([0.25, 0.5, 1, 2]):
        ttk.Button(control_frame, text=f"{rate}x", command=lambda r=rate: change_speed(r)).grid(row=1, column=i + 1, padx=5, pady=5)

    ttk.Button(control_frame, text="Rewind (1/4s)", command=rewind_1_4_sec).grid(row=3, column=0, padx=5, pady=5)
    ttk.Button(control_frame, text="Progress (1/4s)", command=progress_1_4_sec).grid(row=3, column=1, padx=5, pady=5)
    ttk.Button(control_frame, text="Rewind (30s)", command=rewind_30s).grid(row=3, column=2, padx=5, pady=5)
    ttk.Button(control_frame, text="Progress (30s)", command=progress_30s).grid(row=3, column=3, padx=5, pady=5)

    ttk.Label(control_frame, text="Jump to (MM:SS):").grid(row=4, column=0, padx=5, pady=5)
    jump_entry = ttk.Entry(control_frame, width=8)
    jump_entry.grid(row=4, column=1, padx=5, pady=5)
    ttk.Button(control_frame, text="Go", command=jump_to_time).grid(row=4, column=2, padx=5, pady=5)

    sync_status_label = ttk.Label(control_frame, text="", font=("TkDefaultFont", 9, "bold"))
    sync_status_label.grid(row=4, column=3, padx=10, pady=5, sticky="w")

    timer_label = ttk.Label(control_frame, text="00:00 / 00:00")
    timer_label.grid(row=5, column=1, padx=5, pady=5, columnspan=2)

    filename = os.path.basename(files[0])
    display_name = filename[5:] if filename.startswith("CAM") else filename

    parts = filename.split("_")
    if len(parts) >= 3:
        time_part = parts[2][:6]
        try:
            h, m, s = int(time_part[0:2]), int(time_part[2:4]), int(time_part[4:6])
            root.footage_start_time = h * 3600 + m * 60 + s
            logging.debug(f"Parsed footage start time: {h}:{m}:{s}")
        except:
            root.footage_start_time = 0
            logging.warning("Failed to parse footage start time")
    else:
        root.footage_start_time = 0

    ttk.Label(control_frame, text=f"Now playing: {display_name}").grid(row=6, column=0, padx=5, pady=5, columnspan=3)
    overlay_label = ttk.Label(control_frame, text="Footage Time: --:--:--", font=("TkDefaultFont", 10, "bold"))
    overlay_label.grid(row=7, column=0, padx=5, pady=5, columnspan=3, sticky="ew")

    update_timer()
    logging.debug("GUI setup complete. Entering main loop.")
    root.mainloop()

def initialize_players(files):
    options = [
        "--file-caching=1000",
        "--network-caching=1000",
        "--avcodec-hw=none",
        "--no-video-title-show",
        "--quiet"
    ]
    instances = [vlc.Instance(*options) for _ in files]
    for idx, (instance, file) in enumerate(zip(instances, files)):
        logging.debug(f"Setting up player {idx+1} for: {file}")
        player = instance.media_player_new()
        media = instance.media_new(file)
        player.set_media(media)
        player.set_hwnd(frames[idx].winfo_id())
        players.append(player)
        player.play()
        logging.debug(f"Player {idx+1} started for pre-buffering")
    time.sleep(2.0)
    for idx, player in enumerate(players):
        player.pause()
        logging.debug(f"Player {idx+1} paused after pre-buffer")

def play_videos(vlc_path, files):
    logging.debug(f"Launching video playback with VLC path: {vlc_path}")
    create_gui(files)