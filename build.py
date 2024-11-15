import os
import subprocess
import shutil

DEFAULT_APP_NAME = "Video Validation"
DEFAULT_ICON_PATH = "appIcon.ico"

def get_version():
    while True:
        version = input("Enter the version number (e.g., 1.0.0): ").strip()
        confirm = input(f"Confirm version '{version}'? (y/n): ").lower()
        if confirm == 'y':
            return version

def build_app(version, app_name, icon_path):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    output_dir = f"./releases/{version}"
    os.makedirs(output_dir, exist_ok=True)
    app_name_with_version = f"{app_name} {version}"

    command = [
        "pyinstaller",
        "--onefile",
        "--noconsole",
        f"--name={app_name_with_version}",
        f"--distpath={output_dir}",
        "main.py", 
    ]

    if icon_path and os.path.exists(icon_path):
        command.append(f"--icon={icon_path}")

    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command)

    # .spec file in subfolder
    spec_folder = "./specs"
    os.makedirs(spec_folder, exist_ok=True)

    spec_file = f"{app_name}.spec"
    if os.path.exists(spec_file):
        shutil.move(spec_file, os.path.join(spec_folder, spec_file))
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
    version = get_version()
    app_name = input(f"Enter the application name (default: {DEFAULT_APP_NAME}): ").strip() or DEFAULT_APP_NAME
    icon_path = input(f"Enter the path to the icon file (.ico) (default: {DEFAULT_ICON_PATH}): ").strip() or DEFAULT_ICON_PATH

    if not os.path.exists(icon_path):
        print(f"Warning: The icon file '{icon_path}' does not exist. The build will proceed without an icon.\n")

    print(f"\nBuilding version {version} for '{app_name} v{version}'...")
    build_app(version, app_name, icon_path)

    additional_files = ["README.md", "LICENSE"]
    copy_files(version, additional_files)
