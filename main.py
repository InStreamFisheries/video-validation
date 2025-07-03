import os
import sys
import logging
import navigation

def _inject_vlc_bundle():
    base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    vb = os.path.join(base, "vlc_bundle")
    if os.path.isdir(vb):
        os.environ["PATH"] = vb + os.pathsep + os.environ.get("PATH", "")
        os.environ["VLC_PLUGIN_PATH"] = os.path.join(vb, "plugins")

_inject_vlc_bundle()

import video_player

logging.basicConfig(
    level=logging.DEBUG,  # change this to INFO to reduce noise
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # hiding logging for now, uncomment to enable file logging
        # logging.FileHandler("app_debug.log", mode='w'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.debug("main.py initialized.")

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def setup_icon_path():
    icon_path = resource_path("appIcon.ico")
    if not os.path.exists(icon_path):
        logger.warning(f"Icon file not found at {icon_path}. Using default system icons.")
        icon_path = None

    navigation.icon_path = icon_path
    video_player.icon_path = icon_path

def main():
    setup_icon_path()
    navigation.show_navigation_ui()

if __name__ == "__main__":
    main()