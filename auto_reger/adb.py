import random
import logging
import subprocess
import secrets
import time
import string
import base64
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta

from .utils import CONFIG

ADB_PATH_DEFAULT = r"C:\Android\platform-tools\adb.exe"
try:
    ADB_PATH = CONFIG.get("adb", {}).get("adb_path", ADB_PATH_DEFAULT)
except Exception:
    ADB_PATH = ADB_PATH_DEFAULT


USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36... (KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36... (KHTML, like Gecko) Chrome/85.0.4183.127 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36... (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.93 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36... (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36... (KHTML, like Gecko) Chrome/91.0.4472.164 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/72.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/73.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/74.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/12.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/12.1 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/13.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Edge/44.0.2403.119 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Edge/45.0.2454.94 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Edge/46.0.2486.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Opera/58.0.3135.107 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Opera/59.0.3206.125 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Opera/60.0.3255.109 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) UCBrowser/13.2.0.1298 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) UCBrowser/13.3.0.1305 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36... (KHTML, like Gecko) Chrome/84.0.4147.125 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36... (KHTML, like Gecko) Chrome/85.0.4183.127 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36... (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36... (KHTML, like Gecko) Chrome/88.0.4324.181 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36... (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36... (KHTML, like Gecko) Chrome/91.0.4472.164 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/73.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/74.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/75.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/13.2 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Edge/44.0.2403.140 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Edge/45.0.2454.62 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Opera/61.0.3290.111 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Opera/62.0.3331.99 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) UCBrowser/13.4.0.1306 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36... (KHTML, like Gecko) Chrome/92.0.4515.131 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.62 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/76.0 Mobile",
    "Mozilla/5.0 (Linux; Android 9; SM-G781B) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/77.0 Mobile"
]


REAL_DEVICES = [
    {"model": "SM-G960F", "board": "universal9810", "name": "starltexx", "cpu_abi": "arm64-v8a", "hardware": "exynos9810", "full_name": "Samsung Galaxy S9"},
    {"model": "SM-G965F", "board": "universal9810", "name": "star2ltexx", "cpu_abi": "arm64-v8a", "hardware": "exynos9810", "full_name": "Samsung Galaxy S9+"},
    {"model": "SM-N960F", "board": "crownlte", "name": "crownltexx", "cpu_abi": "arm64-v8a", "hardware": "exynos9810", "full_name": "Samsung Galaxy Note9"},
    {"model": "SM-G970F", "board": "beyond0", "name": "beyond0ltexx", "cpu_abi": "arm64-v8a", "hardware": "exynos9820", "full_name": "Samsung Galaxy S10e"},
    {"model": "SM-G973F", "board": "beyond1", "name": "beyond1ltexx", "cpu_abi": "arm64-v8a", "hardware": "exynos9820", "full_name": "Samsung Galaxy S10"},
    {"model": "SM-G975F", "board": "beyond2", "name": "beyond2ltexx", "cpu_abi": "arm64-v8a", "hardware": "exynos9820", "full_name": "Samsung Galaxy S10+"},
    {"model": "SM-A505F", "board": "a50", "name": "a50dd", "cpu_abi": "arm64-v8a", "hardware": "exynos9610", "full_name": "Samsung Galaxy A50"},
    {"model": "SM-A705F", "board": "a70q", "name": "a70q", "cpu_abi": "arm64-v8a", "hardware": "exynos7904", "full_name": "Samsung Galaxy A70"},
    {"model": "SM-G781B", "board": "r8q", "name": "r8qxxx", "cpu_abi": "arm64-v8a", "hardware": "qcom", "full_name": "Samsung Galaxy S20 FE 5G"},
]


def run_adb_command(command: str) -> None:
    """Run a single shell command on the connected Android device via ADB.

    The command is executed inside an interactive "adb shell" with "su"
    to obtain root privileges. Raises RuntimeError on failure.
    """
    try:
        process = subprocess.Popen(
            f'"{ADB_PATH}" shell',
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        # Отправляем команды построчно
        commands = [
            'su',
            command,
            'exit',
            'exit'
        ]

        try:
            stdout, stderr = process.communicate('\n'.join(commands), timeout=10)
            if stderr:
                print(f"Ошибка смены IMEI: {stderr}")
                raise subprocess.CalledProcessError(process.returncode, commands, stderr=stderr)

            logging.info(f"ADB command ran: {stdout}")
        except subprocess.TimeoutExpired as e:
            logging.error(f"Ошибка ADB команды: {e}")
            process.kill()
            raise
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка ADB команды: {e.stderr}")
        raise RuntimeError(f"Ошибка ADB команды: {e.stderr}")


def connect_adb(udid: str, max_attempts: int = 3) -> bool:
    """Try to establish an ADB connection to the given device.

    The function will run ``adb connect`` up to ``max_attempts`` times and
    validate that the device responds with ``echo online``.

    :param udid: Device serial / host:port pair.
    :param max_attempts: Maximum number of connection attempts.
    :return: True if the device responds as online, False otherwise.
    """
    for attempt in range(1, max_attempts + 1):
        print(f"Attempt {attempt}/{max_attempts} to connect to {udid}")
        adb_command = f'"{ADB_PATH}" connect {udid}'
        process = subprocess.Popen(adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        if error:
            print(f"Error connecting to ADB for {udid}: {error.decode()}")
        else:
            print(f"ADB connected to {udid}: {output.decode()}")
            adb_command = f'"{ADB_PATH}" -s {udid} shell echo online'
            process = subprocess.Popen(adb_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, error = process.communicate()
            if not error and "online" in output.decode().strip():
                return True
        time.sleep(2)
    print(f"Failed to connect to {udid} after {max_attempts} attempts")
    return False


def generate_number(nqty):
    number = ''
    for _ in range(nqty):
        number += str(random.randint(0, 9))

    return number


def get_device_info(udid: str) -> dict:
    """Collect basic device information via ADB.

    The function queries Android version, device model, Telegram app version and
    system language. It also tries to map the model to a more user-friendly
    "full name" using the REAL_DEVICES catalogue.

    :param udid: Device serial / host:port pair.
    :return: Dict with keys: ``model``, ``full_model``, ``android``, ``tg``, ``sys_lang``.
    """
    # Android version
    process = subprocess.Popen(f'"{ADB_PATH}" -s {udid} shell getprop ro.build.version.release',
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    android_version = output.decode().strip() if not error else "Unknown"

    # Device model
    process = subprocess.Popen(f'"{ADB_PATH}" -s {udid} shell getprop ro.product.model',
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    device_model = output.decode().strip() if not error else "Unknown"

    # Telegram version (best-effort)
    process = subprocess.Popen(
        f'"{ADB_PATH}" -s {udid} shell dumpsys package org.telegram.messenger | grep versionName',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )
    output, error = process.communicate()
    tg_version = "Unknown"
    if not error:
        line = output.decode().strip()
        if "versionName=" in line:
            tg_version = line.split("versionName=")[-1].strip()

    # System language (locale)
    process = subprocess.Popen(f'"{ADB_PATH}" -s {udid} shell getprop persist.sys.locale',
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    sys_lang = output.decode().strip() if not error else "Unknown"

    # Map model to a full readable name
    try:
        full_model = next(device['full_name'] for device in REAL_DEVICES if device['model'] == device_model)
    except StopIteration:
        # Fallback to a random known device full name if model is not in catalogue
        full_model = random.choice([device['full_name'] for device in REAL_DEVICES])
        logging.warning(f"Model {device_model} not found in REAL_DEVICES, using random full_name: {full_model}")

    return {
        'model': device_model,
        'full_model': full_model,
        'android': 'Android ' + android_version,
        'tg': tg_version,
        'sys_lang': sys_lang
    }


def generate_samsung_imei():
    tac = "35" + ''.join(random.choice('0123456789') for _ in range(6))  # TAC для Samsung
    serial = ''.join(random.choice('0123456789') for _ in range(6))
    temp = tac + serial
    sum_odd = sum(int(temp[i]) for i in range(0, len(temp), 2))
    sum_even = sum(int(d) * 2 if int(d) * 2 < 10 else int(d) * 2 - 9 for d in temp[1::2])
    check_digit = (10 - (sum_odd + sum_even) % 10) % 10
    return temp + str(check_digit)


def generate_samsung_mac():
    oui_list = ["00:03:7A", "00:0D:6F", "00:12:FB", "00:1D:6A"]  # Реальные OUI Samsung
    oui = random.choice(oui_list)
    nic = ':'.join('{:02x}'.format(random.randint(0, 255)) for _ in range(3))
    return oui + ":" + nic


def generate_boottime_sequence(now=None, shift=None):
    if now is None:
        now = datetime.now()

    if shift is None:
        shift = random.randint(0, 60)

    new_time = now - timedelta(minutes=shift)
    return [
        int((new_time - now).total_seconds() * 1000) for minutes in range(-5, 0)
    ]


def change_imei():
    try:
        # Генерация нового IMEI
        new_imei = generate_samsung_imei()

        process = subprocess.Popen(
            "adb shell",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        commands = [
            "su",
            "svc data disable",
            "svc wifi disable",
            "svc bluetooth disable",
            "svc nfc disable",
            "settings put global airplane_mode_on 1",
            "am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true",
            "sleep 2",
            "am broadcast -n com.example.app/.AirplaneModeReceiver --ez state true",
            f"service call iphonesubinfo 7 i32 0 s16 {new_imei}",
            "svc data enable",
            "svc wifi enable",
            "svc bluetooth enable",
            "svc nfc enable",
            "settings put global airplane_mode_on 0",
            "am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false",
            "stop ril-daemon",
            "start ril-daemon",
            "exit",
            "exit"
        ]

        try:
            stdout, stderr = process.communicate('\n'.join(commands), timeout=30)
            if stderr:
                print(f"Ошибка смены IMEI: {stderr}")
                raise subprocess.CalledProcessError(process.returncode, commands, stderr=stderr)

            print(f'New IMEI generated: {new_imei}')
        except subprocess.TimeoutExpired as e:
            print(f"Ошибка смены IMEI: {e}")
            process.kill()
            raise
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to change IMEI: {e.stderr}")
        raise RuntimeError(f"Failed to change IMEI: {e.stderr}")


def generate_android_id():
    return ''.join(secrets.choice('0123456789abcdef') for _ in range(16))


def generate_android_build_id_past():
    start = datetime.now() - timedelta(days=365 * 2)
    end = datetime.now() - timedelta(days=30)

    random_date = start + (end - start) * random.random()

    build_id = random.choice(string.ascii_uppercase)
    build_id += random.choice(string.ascii_uppercase)
    build_id += random_date.strftime('%y%m%d')

    return build_id


def generate_and_set_user_agent() -> str | None:
    """Generate and apply a random User-Agent string on the device.

    Picks a value from the ``USER_AGENTS`` catalogue and updates the built-in
    browser's user agent via ADB + ``settings put``. Returns the new User-Agent
    on success or ``None`` if something went wrong.
    """
    try:
        new_user_agent = random.choice(USER_AGENTS)
        process = subprocess.Popen(
            f'"{ADB_PATH}" shell',
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        commands = [
            "su",
            f"settings put global http_user_agent '{new_user_agent}'",
            "exit",
            "exit"
        ]
        stdout, stderr = process.communicate("\n".join(commands), timeout=10)
        if stderr:
            logging.error(f"Failed to set User-Agent with su: {stderr}")
            return None
        logging.info(f"User-Agent changed to {new_user_agent}")
        return new_user_agent
    except Exception as e:
        logging.error(f"Error setting User-Agent: {str(e)}")
        return None


def change_setting(level, setting_name, value, su=False):
    try:
        if su:
            process = subprocess.Popen(
                "adb shell",
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            commands = [
                "su",
                f"settings put {level} {setting_name} {value}",
                "exit",
                "exit"
            ]
            stdout, stderr = process.communicate("\n".join(commands), timeout=10)
        else:
            process = subprocess.Popen(
                ["adb", "shell", "settings", "put", level, setting_name, str(value)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=10)

        if stderr:
            logging.error(f"Failed to change setting {setting_name}: {stderr}")
            raise subprocess.CalledProcessError(process.returncode, commands if su else [], stderr=stderr)
        logging.info(f"Setting {setting_name} changed to {value}")
    except subprocess.TimeoutExpired as e:
        logging.error(f"Timeout when changing setting {setting_name}: {e}")
        process.kill()
        raise
    except subprocess.CalledProcessError as e:
        logging.error(f"Error changing setting {setting_name}: {e.stderr}")
        raise RuntimeError(f"Error changing setting {setting_name}: {e.stderr}")


def change_prop(setting_name, value, su=False):
    try:
        if su:
            process = subprocess.Popen(
                "adb shell",
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            commands = [
                "su",
                f"setprop {setting_name} {value}",
                "exit",
                "exit"
            ]
            stdout, stderr = process.communicate("\n".join(commands), timeout=10)
        else:
            process = subprocess.Popen(
                ["adb", "shell", "setprop", setting_name, str(value)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=10)

        if stderr:
            logging.error(f"Failed to change prop {setting_name}: {stderr}")
            raise subprocess.CalledProcessError(process.returncode, commands if su else [], stderr=stderr)
        logging.info(f"Prop {setting_name} changed to {value}")
    except subprocess.TimeoutExpired as e:
        logging.error(f"Timeout when changing prop {setting_name}: {e}")
        process.kill()
        raise
    except subprocess.CalledProcessError as e:
        logging.error(f"Error changing prop {setting_name}: {e.stderr}")
        raise RuntimeError(f"Error changing prop {setting_name}: {e.stderr}")


def set_random_timezone():
    try:
        timezones = ["America/New_York", "America/Los_Angeles", "America/Chicago"]
        new_timezone = random.choice(timezones)
        process = subprocess.Popen(
            "adb shell",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        commands = [
            "su",
            f"setprop persist.sys.timezone {new_timezone}",
            "exit",
            "exit"
        ]
        stdout, stderr = process.communicate("\n".join(commands), timeout=10)
        if stderr:
            logging.error(f"Failed to set timezone with su: {stderr}")
            return
        logging.info(f"Timezone changed to {new_timezone}")
    except Exception as e:
        logging.error(f"Error setting timezone: {str(e)}")


def compare_emulator_settings(udid1, udid2):
    try:
        adb_path = r"C:\Android\platform-tools\adb.exe"

        def get_settings(udid, levels=('secure', 'global', 'system')):
            settings = {}
            for level in levels:
                cmd = f'"{adb_path}" -s {udid} shell settings list {level}'
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                output, error = process.communicate()
                if error:
                    logging.error(f"Error reading {level} settings for {udid}: {error.decode()}")
                    continue
                lines = output.decode().splitlines()
                settings[level] = {}
                for line in lines:
                    if '=' in line:
                        k, v = line.split('=', 1)
                        settings[level][k] = v
            return settings

        settings1 = get_settings(udid1)
        settings2 = get_settings(udid2)

        differences = {'secure': {}, 'global': {}, 'system': {}}

        for level in differences.keys():
            keys = set(settings1[level].keys()).union(set(settings2[level].keys()))
            for key in keys:
                val1 = settings1[level].get(key)
                val2 = settings2[level].get(key)
                if val1 != val2:
                    differences[level][key] = {'udid1': val1, 'udid2': val2}

        for level, diffs in differences.items():
            if diffs:
                print(f"Различия в {level} настройках:")
                for key, values in diffs.items():
                    print(f"  {key}:")
                    print(f"    {udid1}: {values['udid1']}")
                    print(f"    {udid2}: {values['udid2']}")

        logging.info(
            f"Сравнение настроек для {udid1} и {udid2} завершено... Найдено различий: {sum(len(d) for d in differences.values())}")
        return differences

    except Exception as e:
        logging.error(f"Ошибка при сравнении настроек: {e}")
        return {}


def generate_stable_secret():
    groups = [''.join(random.choices(string.hexdigits.lower(), k=4)) for _ in range(8)]
    return ':'.join(groups)


def generate_mac_address():
    # Создаем список из 6 случайных шестнадцатеричных чисел (0-255)
    mac_parts = [random.randint(0x00, 0xFF) for _ in range(6)]
    mac_address = ":".join(f"{part:02X}" for part in mac_parts)
    return mac_address


def generate_x509_token():
    try:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"California"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"Mountain View"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Google Inc."),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u"Android"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"Android Build"),
        ])

        certificate = x509.CertificateBuilder()\
            .subject_name(subject)\
            .issuer_name(issuer)\
            .public_key(private_key.public_key())\
            .serial_number(x509.random_serial_number())\
            .not_valid_before(datetime.utcnow())\
            .not_valid_after(datetime.utcnow() + timedelta(days=365 * 10))\
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True
            )\
            .sign(private_key, hashes.SHA256())

        certificate_der = certificate.public_bytes(Encoding.DER)
        certificate_b64 = base64.b64encode(certificate_der).decode()

        return certificate_b64

    except Exception as e:
        logging.error(f"Error generating X.509 token: {e}")
        return None


def reset_data(udid: str, app_for_clear: str, prefix: str | None = None) -> bool:
    """Reset application and device-level identifiers on the Android device.

    This helper will:
      * stop and clear the given application package,
      * reset the Advertising ID,
      * tweak a number of Android settings and system properties (ID, build id,
        language, country, timezone, IMEI, Wi-Fi MAC, etc.).

    It is tailored for Telegram but can be used with any package name that
    supports the same reset pattern.

    :param udid: Device serial / host:port pair.
    :param app_for_clear: Base application package name to clear (e.g. ``org.telegram.messenger``).
    :param prefix: Optional suffix to append to the package name (for cloned apps).
    :return: True on success, False otherwise.
    """
    if prefix:
        app_for_clear += prefix
    try:
        # Check connected devices
        result = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True)
        if "device" not in result.stdout:
            logging.error("No devices found. Ensure USB Debugging is enabled and device is connected.")
            return False

        # If UDID is provided, use it when constructing adb prefix
        adb_prefix = [ADB_PATH, "-s", udid] if udid else [ADB_PATH]

        # Stop the target app
        subprocess.run(adb_prefix + ["shell", "am", "force-stop", app_for_clear], check=True)
        logging.info("Target app closed successfully")

        # Clear app data
        subprocess.run(adb_prefix + ["shell", "pm", "clear", app_for_clear], check=True)
        logging.info("Target app data cleared successfully")

        # Reset Advertising ID
        subprocess.run(adb_prefix + ["shell", "settings", "delete", "secure", "advertising_id"], check=True)
        logging.info("Advertising ID reset successfully")
        # Сброс Advertising ID
        subprocess.run(adb_prefix + ["shell", "pm", "clear", "com.google.android.gms"], check=True)
        logging.info("Google Play Services data cleared successfully")

        new_android_id = generate_android_id()
        new_build_id = generate_android_build_id_past()
        new_cert = generate_x509_token()
        new_mac = generate_mac_address()
        boottimes = generate_boottime_sequence()

        device = random.choice(REAL_DEVICES)

        change_setting('secure', 'android_id', new_android_id)
        change_setting('secure', 'advertising_id', new_android_id)
        change_setting('secure', 'config_update_certificate', new_cert)
        change_setting('global', 'database_creation_buildid', new_build_id)
        change_prop('persist.sys.language', 'en')
        change_prop('persist.sys.country', 'US')
        change_prop('persist.sys.locale', 'en-US')
        change_prop('ro.product.cpu.abi', device['cpu_abi'])
        change_prop('wifi.interface.mac', new_mac)
        change_prop('ro.hardware', device['hardware'])
        change_prop('ro.product.model', device['model'])
        change_prop('ro.product.board', device['board'])
        change_prop('ro.product.name', device['name'])
        change_prop('ro.boottime.init', boottimes[-1])
        set_random_timezone()
        change_imei()
        run_adb_command('am broadcast -a android.intent.action.LOCALE_CHANGED')

        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to reset Telegram data: {e}")
        return False
    except Exception as e:
        logging.error(f"Error during Telegram data reset: {e}")
        return False


if __name__ == '__main__':
    reset_data('XED4C18515000819', 'org.telegram.messenger')
