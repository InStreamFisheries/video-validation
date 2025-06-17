import vlc
import os
import tkinter as tk
from tkinter import ttk
import time
from time import monotonic as now
import sys

players = []
frames = []
current_speed = 1
speed_buttons = []
window_base_title = ""
skip_configurable_seconds = 10
control_widgets = []
skip_in_progress = False

playback_start_monotonic = 0
manual_offset = 0

WATCHDOG_ENABLED = True
WATCHDOG_INTERVAL_MS = 200

DEBUG_LOGGING = True

def log(msg):
    if DEBUG_LOGGING:
        print(f"[DEBUG] {time.strftime('%H:%M:%S')} — {msg}")


def pause_all_players():
    global playback_start_monotonic, manual_offset
    if playback_start_monotonic > 0:
        offset = (now() - playback_start_monotonic) * current_speed
        manual_offset += offset
        log(f"Paused — added {offset:.2f}s to manual_offset (now {manual_offset:.2f})")
    playback_start_monotonic = 0

    for idx, player in enumerate(players):
        try:
            player.pause()
            state = player.get_state()
            log(f"Player {idx} paused — state: {state}")
        except Exception as e:
            log(f"Player {idx} pause failed: {e}")


def play_all_players():
    global playback_start_monotonic
    for idx, player in enumerate(players):
        try:
            player.play()
            log(f"Player {idx} play called")
            log(f"Player {idx} state after initial play: {player.get_state()}")
        except Exception as e:
            log(f"Player {idx} play failed: {e}")
    playback_start_monotonic = now()
    log("Playback started — timer resumed")

def toggle_play_pause():
    if any(player.is_playing() for player in players):
        log("Toggle: pausing")
        pause_all_players()
        root.title(f"{window_base_title} — PAUSED")
    else:
        log("Toggle: playing")
        play_all_players()
        root.title(f"{window_base_title} — PLAYING")

def change_speed(rate):
    for player in players:
        try:
            player.set_rate(rate)
        except:
            pass

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

def watchdog_enforce_paused():
    if not WATCHDOG_ENABLED or not players:
        root.after(WATCHDOG_INTERVAL_MS, watchdog_enforce_paused)
        return

    if playback_start_monotonic == 0:
        for idx, player in enumerate(players):
            try:
                if player.is_playing():
                    log(f"[WATCHDOG] Player {idx} unexpectedly playing — forcing pause")
                    player.set_pause(True)
            except Exception as e:
                log(f"[WATCHDOG] Error checking player {idx}: {e}")

    root.after(WATCHDOG_INTERVAL_MS, watchdog_enforce_paused)

def update_timer():
    global playback_start_monotonic

    if not players:
        root.after(500, update_timer)
        return

    playing = any(player.is_playing() for player in players)

    if playback_start_monotonic > 0 and playing:
        elapsed_since_play = (now() - playback_start_monotonic) * current_speed
    else:
        elapsed_since_play = 0

    current_time_sec = int(elapsed_since_play + manual_offset)

    log(f"update_timer: {current_time_sec}s (manual_offset={manual_offset:.2f}, playback_start_monotonic={playback_start_monotonic:.2f})")
    minutes, seconds = divmod(current_time_sec, 60)

    try:
        duration_ms = players[0].get_length()
    except:
        duration_ms = -1

    if duration_ms <= 0:
        timer_label.config(text="--:-- / --:--")
        root.after(500, update_timer)
        return

    duration_sec = duration_ms // 1000
    duration_minutes, duration_seconds = divmod(duration_sec, 60)

    timer_label.config(text=f"{minutes:02}:{seconds:02} / {duration_minutes:02}:{duration_seconds:02}")

    if hasattr(root, "footage_start_time"):
        total_seconds = root.footage_start_time + current_time_sec
        hr, rem = divmod(total_seconds, 3600)
        mn, sc = divmod(rem, 60)
        overlay_label.config(text=f"Footage Time: {hr:02}:{mn:02}:{sc:02}")

    root.after(500, update_timer)

def skip_all_players(seconds):
    global skip_in_progress, manual_offset, playback_start_monotonic

    if skip_in_progress:
        log("Skip ignored — already in progress")
        return

    skip_in_progress = True
    set_controls_enabled(False)

    log(f"Skip requested: {seconds:+} seconds")
    pause_all_players()
    manual_offset += seconds
    log(f"Manual offset updated to: {manual_offset:.2f}s")

    target_time_ms = max(0, int(manual_offset * 1000))
    for idx, player in enumerate(players):
        try:
            duration = player.get_length()
            seek_time = min(target_time_ms, duration)
            log(f"Player {idx}: seeking to {seek_time} (duration {duration})")

            for attempt in range(2):
                player.set_time(seek_time)
                actual = player.get_time()
                if actual < 0:
                    actual = 0
                if abs(actual - seek_time) <= 250:
                    break
                log(f"Player {idx}: seek diff {abs(actual - seek_time)}ms, retrying")
                time.sleep(0.1)
        except Exception as e:
            log(f"[WARNING] Player {idx} skip failed: {e}")

    playback_start_monotonic = 0
    update_timer()

    def enforce_pause(attempts=6):
        if attempts <= 0:
            log("[FORCED PAUSE] Max attempts reached — giving up.")
            return

        still_playing = False
        for idx, player in enumerate(players):
            try:
                state = player.get_state()
                if state == vlc.State.Playing:
                    player.set_pause(True)
                    log(f"[FORCED PAUSE] Player {idx} still playing — re-paused (attempts left: {attempts - 1})")
                    still_playing = True
                else:
                    log(f"Player {idx} state: {state}")
            except Exception as e:
                log(f"Error enforcing pause on player {idx}: {e}")

        if still_playing:
            root.after(200, lambda: enforce_pause(attempts - 1))

    root.after(300, lambda: enforce_pause(attempts=6))

    def finish_skip():
        global skip_in_progress
        skip_in_progress = False
        set_controls_enabled(True)
        log("Skip complete — controls re-enabled")

    root.after(1600, finish_skip)


def set_controls_enabled(enabled):
    state = "normal" if enabled else "disabled"
    for widget in control_widgets:
        try:
            widget.config(state=state)
        except:
            pass

def skip_back_configurable():
    skip_all_players(-skip_configurable_seconds)

def skip_forward_configurable():
    skip_all_players(skip_configurable_seconds)

def on_closing():
    print("on_closing called")
    for player in players:
        try:
            player.stop()
            player.release()
        except Exception as e:
            print(f"Error stopping player: {e}")
    players.clear()
    try:
        if root.winfo_exists():
            root.destroy()
    except Exception as e:
        print(f"Error destroying window: {e}")

def stop_app():
    global manual_offset, playback_start_monotonic
    manual_offset = 0
    playback_start_monotonic = 0
    on_closing()

def create_gui(files, icon_path=None):
    global root, frames, timer_label, overlay_label
    global current_speed, speed_buttons, window_base_title
    global skip_configurable_seconds, control_widgets

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

    root.bind("<Left>", lambda e: skip_back_configurable())
    root.bind("<Right>", lambda e: skip_forward_configurable())

    try:
        root.attributes("-zoomed", True)
    except:
        root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")

    num_videos = len(files)
    cols = int(num_videos ** 0.5 + 0.5)
    rows = (num_videos + cols - 1) // cols

    for r in range(rows):
        root.grid_rowconfigure(r, weight=10)
    root.grid_rowconfigure(rows, weight=1)
    for c in range(cols):
        root.grid_columnconfigure(c, weight=1)

    frames.clear()
    for idx in range(num_videos):
        row, col = divmod(idx, cols)
        frame = tk.Frame(root, bg="black")
        frame.grid(row=row, column=col, sticky="nsew")
        frame.grid_propagate(False)
        frames.append(frame)

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
    control_frame.configure(height=100)

    btn_playpause = tk.Button(control_frame, text="Play/Pause", command=toggle_play_pause)
    btn_playpause.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    control_widgets.append(btn_playpause)

    btn_stop = tk.Button(control_frame, text="Stop", command=stop_app)
    btn_stop.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    control_widgets.append(btn_stop)

    skip_frame = tk.Frame(control_frame)
    skip_frame.grid(row=1, column=0, columnspan=4, sticky="w", padx=5, pady=5)

    btn_back = tk.Button(skip_frame, text="<<", command=skip_back_configurable)
    btn_back.pack(side="left", padx=(2, 5))
    control_widgets.append(btn_back)

    def update_skip_value(selected):
        global skip_configurable_seconds
        try:
            skip_configurable_seconds = int(selected)
        except ValueError:
            pass

    skip_options = ["1", "5", "10", "15", "30", "60"]
    skip_dropdown = ttk.Combobox(skip_frame, values=skip_options, width=4, state="readonly")
    skip_dropdown.set(str(skip_configurable_seconds))
    skip_dropdown.pack(side="left", padx=2)
    skip_dropdown.bind("<<ComboboxSelected>>", lambda e: update_skip_value(skip_dropdown.get()))
    control_widgets.append(skip_dropdown)

    btn_forward = tk.Button(skip_frame, text=">>", command=skip_forward_configurable)
    btn_forward.pack(side="left", padx=(5, 2))
    control_widgets.append(btn_forward)

    speed_frame = tk.Frame(control_frame)
    speed_frame.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=5)

    tk.Label(speed_frame, text="Speed:").pack(side="left", padx=5)

    speed_buttons.clear()
    for rate in [0.25, 0.5, 1, 2]:
        btn = tk.Button(speed_frame, text=f"{rate}x", command=lambda r=rate: set_speed(r))
        btn.pack(side="left", padx=2)
        speed_buttons.append((rate, btn))
        control_widgets.append(btn)

    update_speed_button_styles()

    control_frame.grid_columnconfigure(1, weight=1)
    control_frame.grid_columnconfigure(2, weight=1)

    timer_label = ttk.Label(control_frame, text="00:00 / 00:00")
    timer_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")

    overlay_label = ttk.Label(control_frame, text="Footage Time: --:--:--", font=("TkDefaultFont", 12, "bold"))
    overlay_label.grid(row=5, column=3, padx=5, pady=5, sticky="e")

    filename = os.path.basename(files[0])
    display_name = filename[5:] if filename.startswith("CAM") else filename
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
                print(f"[WARNING] Failed to parse footage time: {e}")

    set_controls_enabled(False)
    root.withdraw()
    root.after(100, lambda: initialize_players(files))
    update_timer()
    watchdog_enforce_paused()


def wait_for_playback_ready(player, tries_left=15):
    try:
        state = player.get_state()
    except:
        state = vlc.State.Error

    if state == vlc.State.Playing or tries_left <= 0:
        try:
            player.pause()
        except:
            pass
        root.update()
    else:
        root.after(100, lambda: wait_for_playback_ready(player, tries_left - 1))

def initialize_players(files, icon_path=None):
    global players, manual_offset, playback_start_monotonic, current_speed
    manual_offset = 0
    playback_start_monotonic = 0
    current_speed = 1.0
    
    for player in players:
        try:
            player.release()
        except:
            pass
    players.clear()

    loading_popup = tk.Toplevel(root)
    loading_popup.title("Loading Videos...")
    loading_popup.geometry("300x100")
    tk.Label(loading_popup, text="Loading videos...\nPlease wait.").pack(expand=True)
    loading_popup.update()

    instances = [vlc.Instance(
        "--file-caching=1000",
        "--network-caching=1000",
        "--avcodec-hw=none",
        "--no-video-title-show",
        "--quiet"
    ) for _ in files]

    for instance, file, frame in zip(instances, files, frames):
        try:
            print(f"Initializing player for {file}")
            player = instance.media_player_new()
            media = instance.media_new(file)
            player.set_media(media)
            
            window_id = frame.winfo_id()
            try:
                if os.name == "nt" or sys.platform.startswith("win"):
                    player.set_hwnd(window_id)
                elif sys.platform.startswith("linux"):
                    player.set_xwindow(window_id)
                elif sys.platform == "darwin":
                    player.set_nsobject(window_id)
                else:
                    log(f"Unsupported platform: {sys.platform}")
            except Exception as e:
                log(f"Failed to set window handle on {sys.platform}: {e}")

            players.append(player)
            player.play()
            root.update()
            wait_for_playback_ready(player)
            print(f"  --> {file} ready")
        except Exception as e:
            print(f"[ERROR] Failed to init player for {file}: {e}")

    loading_popup.destroy()
    root.deiconify()
    root.focus_force()
    set_controls_enabled(True)

def play_videos(vlc_path, files, icon_path=None):
    create_gui(files, icon_path)