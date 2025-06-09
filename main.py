import os
import navigation
import video_player


def setup_icon_path():
    icon_path = os.path.join(os.path.dirname(__file__), "appIcon.ico")
    if not os.path.exists(icon_path):
        print(f"Warning: Icon file not found at {icon_path}. Using default system icons.")
        icon_path = None  # fallback to default system icon

    # assigning icon to other files, refactoring def
    navigation.icon_path = icon_path
    video_player.icon_path = icon_path

def main():
    setup_icon_path()
    navigation.show_navigation_ui()

if __name__ == "__main__":
    main()
