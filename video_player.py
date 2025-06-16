import vlc
import os
import tkinter as tk
from tkinter import ttk
import time

players = []
frames = []
current_speed = 1
speed_buttons = []
window_base_title = ""

def pause_all_players():
    for player in players:
        player.pause()

def play_all_players():
    for player in players:
        player.play()

def toggle_play_pause():
    if any(player.is_playing() for player in players):
        pause_all_players()
        root.title(f"{window_base_title} — PAUSED")
    else:
        play_all_players()
        root.title(f"{window_base_title} — PLAYING")

def change_speed(rate):
    for player in players:
        player.set_rate(rate)

def set_speed(r):
    global current_speed
    current_speed = r
    change_speed(r)
    update_speed_button_styles()

def update_speed_button_styles():
    for rate, btn in speed_buttons:
        if rate == current_speed:
            btn.config(relief="sunken", font=("TkDefaultFont", 10, "bold"), foreground="blue")
        else:
            btn.config(relief="raised", font=("TkDefaultFont", 10), foreground="black")

def update_timer():
    if players:
        current_time_ms = sum(player.get_time() for player in players) // len(players)
        current_time_sec = current_time_ms // 1000
        minutes, seconds = divmod(current_time_sec, 60)

        duration_ms = players[0].get_length()
        if duration_ms <= 0:
            root.after(1000, update_timer)
            return
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
    print("on_closing called")
    for player in players:
        try:
            player.stop()
        except Exception as e:
            print(f"Error stopping player: {e}")
    players.clear()

    try:
        if root.winfo_exists():
            root.destroy()
    except Exception as e:
        print(f"Error destroying window: {e}")

def stop_app():
    on_closing()

def create_gui(files, icon_path=None):
    global root, frames, timer_label, overlay_label
    global current_speed, speed_buttons, window_base_title

    root = tk.Toplevel()
    root.title("Video Player")

    try:
        if icon_path:
            if icon_path.endswith(".ico") and os.name == "nt":
                root.iconbitmap(icon_path)
            else:
                img = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, img)
    except Exception as e:
        print(f"Failed to set video player icon: {e}")

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.bind("<Return>", lambda e: toggle_play_pause())
    root.bind("<F11>", lambda e: root.attributes("-fullscreen", not root.attributes("-fullscreen")))

    try:
        root.state('zoomed')
    except:
        pass

    num_videos = len(files)
    cols = int(num_videos ** 0.5 + 0.5)
    rows = (num_videos + cols - 1) // cols

    for r in range(rows):
        root.grid_rowconfigure(r, weight=10)

    root.grid_rowconfigure(rows, weight=1)

    for c in range(cols):
        root.grid_columnconfigure(c, weight=1)

    frames = []
    for idx in range(num_videos):
        row, col = divmod(idx, cols)
        frame = tk.Frame(root, bg="black")
        frame.grid(row=row, column=col, sticky="nsew")
        frame.grid_propagate(False)
        frames.append(frame)

    # add bottom-right overlay boxes in the root window
    overlay_frames = []
    for idx, frame in enumerate(frames):
        overlay = tk.Frame(root, bg="black")
        overlay_frames.append(overlay)

        def place_overlay(event=None, overlay=overlay, frame=frame):
            frame.update_idletasks()
            x = frame.winfo_rootx() - root.winfo_rootx()
            y = frame.winfo_rooty() - root.winfo_rooty()
            w = frame.winfo_width()
            h = frame.winfo_height()
            box_width = int(w * 0.4)
            box_height = int(h * 0.1)
            box_x = x + w - box_width - 10
            box_y = y + h - box_height - 10
            overlay.place(x=box_x, y=box_y, width=box_width, height=box_height)

        frame.bind("<Configure>", place_overlay)
        root.after(500, place_overlay)

    control_frame = tk.Frame(root)
    control_frame.grid(row=rows, column=0, columnspan=cols, sticky="nsew")
    control_frame.grid_propagate(False)
    control_frame.configure(height=80)

    tk.Button(control_frame, text="Play/Pause", command=toggle_play_pause).grid(row=0, column=0, padx=5, pady=5, sticky="w")
    tk.Button(control_frame, text="Stop", command=stop_app).grid(row=0, column=1, padx=5, pady=5, sticky="w")

    speed_frame = tk.Frame(control_frame)
    speed_frame.grid(row=1, column=0, columnspan=4, sticky="w", padx=5, pady=5)

    tk.Label(speed_frame, text="Speed:").pack(side="left", padx=5)

    speed_buttons = []
    for rate in [0.25, 0.5, 1, 2]:
        btn = tk.Button(speed_frame, text=f"{rate}x", command=lambda r=rate: set_speed(r))
        btn.pack(side="left", padx=2)
        speed_buttons.append((rate, btn))

    update_speed_button_styles()

    control_frame.grid_columnconfigure(1, weight=1)
    control_frame.grid_columnconfigure(2, weight=1)

    timer_label = ttk.Label(control_frame, text="00:00 / 00:00")
    timer_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")

    overlay_label = ttk.Label(control_frame, text="Footage Time: --:--:--", font=("TkDefaultFont", 12, "bold"))
    overlay_label.grid(row=5, column=3, padx=5, pady=5, sticky="e")

    filename = os.path.basename(files[0])
    display_name = filename
    if filename.startswith("CAM"):
        display_name = filename[5:]

    window_base_title = f"Video Player — {display_name} loaded"
    root.title(f"{window_base_title} — PAUSED")

    root.footage_start_time = 0
    parts = filename.split("_")
    if len(parts) >= 3:
        time_str = parts[2].split(".")[0]
        if time_str.isdigit():
            try:
                h = int(time_str[0:2])
                m = int(time_str[2:4])
                s = int(time_str[4:6]) if len(time_str) >= 6 else 0
                root.footage_start_time = h * 3600 + m * 60 + s
                print(f"[DEBUG] Parsed footage start time: {h:02}:{m:02}:{s:02}")
            except Exception as e:
                print(f"[WARNING] Failed to parse footage start time: {e}")
        else:
            print(f"[DEBUG] Invalid time part in filename: {time_str}")
    else:
        print(f"[DEBUG] Filename does not follow expected pattern: {filename}")

    root.after(100, lambda: initialize_players(files, icon_path))
    update_timer()

def initialize_players(files, icon_path=None):
    print("Initializing players for files:")
    for f in files:
        print(f"  --> {f}")

    loading_popup = tk.Toplevel(root)
    loading_popup.title("Loading Videos...")

    try:
        if icon_path:
            if icon_path.endswith(".ico") and os.name == "nt":
                loading_popup.iconbitmap(icon_path)
            else:
                img = tk.PhotoImage(file=icon_path)
                loading_popup.iconphoto(True, img)
    except Exception as e:
        print(f"Failed to set loading popup icon: {e}")

    loading_popup.geometry("300x100")
    loading_popup.transient(root)
    loading_popup.grab_set()
    loading_popup.resizable(False, False)

    tk.Label(loading_popup, text="Loading videos...\nPlease wait.").pack(expand=True)
    loading_popup.update()

    loading_popup.update_idletasks()
    w = loading_popup.winfo_width()
    h = loading_popup.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    loading_popup.geometry(f"+{x}+{y}")

    options = [
        "--file-caching=1000",
        "--network-caching=1000",
        "--avcodec-hw=none",
        "--no-video-title-show",
        "--quiet"
    ]
    instances = [vlc.Instance(*options) for _ in files]
    for instance, file, frame in zip(instances, files, frames):
        print(f"\nCreating player for: {file}")
        player = instance.media_player_new()
        media = instance.media_new(file)
        player.set_media(media)
        print(f"  --> Media set for {file}")
        hwnd = frame.winfo_id()
        print(f"  --> hwnd for frame: {hwnd}")
        player.set_hwnd(hwnd)
        players.append(player)
        player.play()
        root.update()

        for i in range(10):
            state = player.get_state()
            print(f"    Pre-buffer check {i}: player state = {state}")
            if state == vlc.State.Playing:
                print(f"    Detected State.Playing, waiting 0.15 sec to let frame render...")
                time.sleep(0.15)
                break
            if state not in (vlc.State.Opening, vlc.State.NothingSpecial):
                break
            time.sleep(0.1)

        player.pause()
        final_state = player.get_state()
        print(f"  --> Player paused for {file}, final state: {final_state}")

        if final_state in (vlc.State.Error, vlc.State.Opening):
            print(f"  --> Player failed to load ({final_state}), retrying once...")
            player.stop()
            player.set_media(media)
            player.set_hwnd(hwnd)
            player.play()
            root.update()
            for i in range(10):
                state = player.get_state()
                print(f"    Retry pre-buffer check {i}: player state = {state}")
                if state == vlc.State.Playing:
                    print(f"    Detected State.Playing on retry, waiting 0.15 sec to let frame render...")
                    time.sleep(0.15)
                    break
                if state not in (vlc.State.Opening, vlc.State.NothingSpecial):
                    break
                time.sleep(0.1)
            player.pause()
            final_state = player.get_state()
            print(f"  --> Retry complete, final state: {final_state}")

    loading_popup.grab_release()
    loading_popup.destroy()
    root.focus_force()

def play_videos(vlc_path, files, icon_path=None):
    create_gui(files, icon_path)