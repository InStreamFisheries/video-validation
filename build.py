import os
import sys
import subprocess
import shutil

app_name = "Video Validation"
icon_path = os.path.join(os.path.dirname(__file__), "appIcon.ico")

def validate_icon_path():
    global icon_path
    if not os.path.exists(icon_path):
        print(f"Warning: Default icon file '{icon_path}' not found.")
        user_icon_path = input("Enter the path to the icon file (.ico), or press Enter to skip: ").strip()
        if user_icon_path and os.path.exists(user_icon_path):
            icon_path = user_icon_path
        else:
            print("No valid icon provided. The build will proceed without an icon.")
            icon_path = None

def get_version():
    while True:
        version = input("Enter the version number (e.g., 1.0.0): ").strip()
        confirm = input(f"Confirm version '{version}'? (y/n): ").lower()
        if confirm == 'y':
            return version

def build_app(version):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    output_dir = f"./releases/{version}"
    os.makedirs(output_dir, exist_ok=True)
    app_name_with_version = f"{app_name} {version}"

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        f"--name={app_name_with_version}",
        f"--distpath={output_dir}",
        "main.py",
    ]

    if icon_path:
        icon_full = os.path.abspath(icon_path)
        command.extend([f"--icon={icon_full}", f"--add-data={icon_full};."])

    # add VLC .dlls and plugins from ./vlc_bundle/
    vlc_dir = os.path.abspath("vlc_bundle")
    if os.path.exists(vlc_dir):
        dll1 = os.path.join(vlc_dir, "libvlc.dll")
        dll2 = os.path.join(vlc_dir, "libvlccore.dll")
        plugins_dir = os.path.join(vlc_dir, "plugins")

        if os.path.exists(dll1):
            command.append(f"--add-data={dll1};.")
        if os.path.exists(dll2):
            command.append(f"--add-data={dll2};.")
        if os.path.exists(plugins_dir):
            command.append(f"--add-data={plugins_dir};plugins")

    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command)

    # Move the .spec file to the 'specs' folder
    spec_folder = "./specs"
    os.makedirs(spec_folder, exist_ok=True)
    spec_file = f"{app_name_with_version}.spec"
    spec_file_path = os.path.join(os.getcwd(), spec_file)
    if os.path.exists(spec_file_path):
        shutil.move(spec_file_path, os.path.join(spec_folder, spec_file))
        print(f"Moved .spec file to {spec_folder}")

    if result.returncode == 0:
        print(f"Build completed successfully. Files are in {output_dir}")
    else:
        print("Build failed. Check the output for details.")

def copy_files(version, files_to_copy):
    output_dir = f"./releases/{version}"
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy(file, output_dir)
            print(f"Copied {file} to {output_dir}")

if __name__ == "__main__":
    validate_icon_path()
    version = get_version()

    print(f"\nBuilding version {version} for '{app_name} {version}'...")
    build_app(version)

    additional_files = ["README.md", "LICENSE"]
    copy_files(version, additional_files)
