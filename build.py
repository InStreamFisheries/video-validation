import os
import subprocess
import shutil

app_name = "Video Validation"
source_script = "main.py"
default_icon = os.path.join(os.path.dirname(__file__), "appIcon.ico")

embedded_files = [
    "version.txt",
    "appIcon.ico"
]

def validate_icon_path():
    global default_icon
    if not os.path.exists(default_icon):
        print(f"Warning: Default icon file '{default_icon}' not found.")
        user_icon_path = input("Enter path to icon file (.ico), or press Enter to skip: ").strip()
        if user_icon_path and os.path.exists(user_icon_path):
            default_icon = user_icon_path
        else:
            print("No valid icon provided. The build will proceed without an icon.")
            default_icon = None

def get_version():
    previous_version = "unknown"
    version_file = "version.txt"
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            previous_version = f.read().strip()

    while True:
        version = input(f"Enter the version number (prev. app version: {previous_version}): ").strip()
        confirm = input(f"Confirm version '{version}'? (y/n): ").strip().lower()
        if confirm == 'y':
            return version

def build_app(version):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    app_folder_name = app_name
    release_dir = os.path.join("releases", app_folder_name, version)
    build_dir = os.path.join("build", app_folder_name, version)
    spec_dir = os.path.join("specs", app_folder_name, version)

    os.makedirs(release_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(spec_dir, exist_ok=True)

    exe_name = f"{app_name} {version}"

    command = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--noconsole",
        f"--name={exe_name}",
        f"--distpath={release_dir}",
        f"--workpath={build_dir}",
        f"--specpath={spec_dir}",
        source_script,
    ]

    for file in embedded_files:
        file_path = os.path.join(os.getcwd(), file)
        if os.path.exists(file_path):
            if file == "version.txt":
                command.append(f"--add-data={file_path}{os.pathsep}version.txt")
            else:
                command.append(f"--add-data={file_path}{os.pathsep}.")

    vlc_dir = os.path.abspath("vlc_bundle")
    if os.path.isdir(vlc_dir):
        command.append(f"--add-data={vlc_dir}{os.pathsep}vlc_bundle")

    if default_icon:
        command.append(f"--icon={default_icon}")

    print("\n[BUILD COMMAND]")
    print(" ".join(command))
    result = subprocess.run(command)

    if result.returncode == 0:
        print(f"\nBuild complete. Output in: {release_dir}")
    else:
        print("\nBuild failed. See the output above for errors.")

def copy_files(version, files_to_copy):
    release_dir = os.path.join("releases", app_name, version)
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy(file, release_dir)
            print(f"Copied {file} → {release_dir}")

if __name__ == "__main__":
    validate_icon_path()
    version = get_version()

    with open("version.txt", "w") as f:
        f.write(version)

    print(f"\nBuilding '{app_name}' version {version}...\n")
    build_app(version)

    additional_files = ["README.md", "LICENSE"]
    copy_files(version, additional_files)