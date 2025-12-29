import json
import logging
import os
import random
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import psutil
import requests
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = PROJECT_ROOT / "log.txt"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
    encoding="utf-8",
)


def load_config(config_name: str = "config.yaml") -> Dict[str, Any]:
    """
    Load YAML configuration from the project root.

    By default, looks for PROJECT_ROOT / config_name.
    You can later switch this to config/config.yaml if needed.
    """
    config_path = PROJECT_ROOT / config_name

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


CONFIG: Dict[str, Any] = load_config()


def read_json(path: str) -> Any:
    """
    Read a JSON file and return the Python object.

    :param path: Path to the JSON file.
    :return: Parsed Python object.
    """
    with open(path, "r", encoding="utf-8") as f_o:
        return json.load(f_o)


def write_json(obj: Any, path: str) -> None:
    """
    Write a Python object to a JSON file with indentation.

    Parent directories will be created automatically if needed.

    :param obj: Python object to serialize.
    :param path: Target file path.
    """
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f_o:
        json.dump(obj, f_o, indent=4)


def read_txt(file_path: str) -> str:
    """
    Read a text file and return its full content as a single string.

    :param file_path: Path to the text file.
    :return: File content as string.
    """
    with open(file_path, "r", encoding="utf-8") as f_o:
        return f_o.read()


def read_txt_list(file_path: str) -> List[str]:
    """
    Read a text file and return a list of lines.

    Newlines are preserved as in file.readlines().

    :param file_path: Path to the text file.
    :return: List of lines.
    """
    with open(file_path, "r", encoding="utf-8") as f_o:
        return f_o.readlines()


def load_names(file_path: str) -> List[str]:
    """
    Load a list of names from a text file (one name per line).

    Empty lines and pure whitespace are ignored.

    :param file_path: Path to the names file.
    :return: List of normalized names.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def generate_random_string(length: int = 8) -> str:
    """
    Generate a random lowercase ASCII string.

    :param length: Length of the output string.
    :return: Random string.
    """
    import string

    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def download_random_avatar(file_name: str = "face.jpg") -> str:
    """
    Download a random avatar image from thispersondoesnotexist.com.

    :param file_name: Local file name to save the image as.
    :return: Path to the saved file (same as file_name).
    :raises RuntimeError: If the request fails.
    """
    url = "https://thispersondoesnotexist.com/"
    r = requests.get(url)

    if r.status_code == 200:
        with open(file_name, "wb") as f:
            f.write(r.content)
        logging.info("Saved random avatar to %s", file_name)
        return file_name

    raise RuntimeError("Failed to download avatar image from thispersondoesnotexist.com")


def save_instagram_data(new_data: Dict[str, Any]) -> None:
    """
    Append Instagram account data to a daily JSON file.

    Files are stored in PROJECT_ROOT / "instagram" directory.
    Each day has its own file: YYYY-MM-DD_accounts.json.

    :param new_data: Dict with Instagram account data to append.
    """
    data_dir = PROJECT_ROOT / "instagram"
    data_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    today_file_name = data_dir / f"{today}_accounts.json"

    if today_file_name.exists():
        with open(today_file_name, "r", encoding="utf-8") as f:
            accounts = json.load(f)
    else:
        accounts = []

    accounts.append(new_data)

    with open(today_file_name, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=4)


def get_device_config(num_threads: int, is_physical: bool) -> List[Dict[str, Any]]:
    """
    Build a list of device configurations for Appium sessions.

    For physical device:
        - Reads UDID and Appium port from CONFIG["adb"].
    For emulator:
        - Asks for emulator app path and process name;
        - Asks for Appium port for each emulator instance.

    :param num_threads: Number of parallel sessions / emulators.
    :param is_physical: True if using a single physical device, False for emulators.
    :return: List of device configuration dicts.
    """
    devices: List[Dict[str, Any]] = []

    if is_physical:
        udid = CONFIG["adb"]["device_udid"]
        if not udid:
            raise ValueError("UDID cannot be empty for physical device")

        port = CONFIG["adb"]["appium_port"]
        try:
            port = int(port)
            if port < 1024 or port > 65535:
                raise ValueError("Port must be between 1024 and 65535")
        except ValueError as exc:
            raise ValueError("Invalid port number in config for Appium") from exc

        devices.append(
            {
                "is_physical": True,
                "udid": udid,
                "appium_port": port,
                "app_path": None,
                "app_name": None,
            }
        )
    else:
        emulator_app_path = (
            input(
                "Enter emulator app path "
                "(default: C:\\LDPlayer\\LDPlayer9\\dnplayer.exe): "
            ).strip()
            or r"C:\LDPlayer\LDPlayer9\dnplayer.exe"
        )

        emulator_app_name = (
            input("Enter emulator process name (default: dnplayer.exe): ").strip()
            or "dnplayer.exe"
        )

        for i in range(num_threads):
            port_str = (
                input(
                    f"Enter Appium port for emulator {i + 1} (default 4723): "
                ).strip()
                or "4723"
            )
            try:
                port = int(port_str)
                if port < 1024 or port > 65535:
                    raise ValueError(
                        f"Port for emulator {i + 1} must be between 1024 and 65535"
                    )
            except ValueError as exc:
                raise ValueError(
                    f"Invalid port number for emulator {i + 1}: {port_str!r}"
                ) from exc

            devices.append(
                {
                    "is_physical": False,
                    "udid": None,
                    "appium_port": port,
                    "app_path": emulator_app_path,
                    "app_name": emulator_app_name,
                }
            )

    return devices


def _is_process_running(process_name: str) -> bool:
    """
    Check whether a process with a given name is running.

    :param process_name: Executable name, e.g. 'dnplayer.exe'.
    :return: True if process is running, False otherwise.
    """
    for proc in psutil.process_iter(["name"]):
        if proc.info.get("name", "").lower() == process_name.lower():
            return True
    return False


def kill_emulator(app_name: str) -> None:
    """
    Terminate emulator process by name using taskkill on Windows.

    No error is raised if the process is not running.

    :param app_name: Executable name, e.g. 'dnplayer.exe'.
    """
    if _is_process_running(app_name):
        subprocess.run(
            f"taskkill /IM {app_name} /F",
            shell=True,
            capture_output=True,
        )
        time.sleep(2)
        logging.info("Emulator %s terminated", app_name)
    else:
        logging.info("Emulator %s is not running, nothing to terminate", app_name)


if __name__ == "__main__":
    download_random_avatar()
