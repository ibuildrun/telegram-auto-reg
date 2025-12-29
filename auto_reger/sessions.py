import asyncio
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from telethon.sessions import SQLiteSession, MemorySession
from telethon.sync import TelegramClient
from telethon.crypto import AuthKey
from telethon.errors import (
    FloodError,
    PasswordHashInvalidError,
    SessionPasswordNeededError,
)

from TGConvertor.manager import SessionManager
from AndroidTelePorter import AndroidSession

from .tdesktop import get_auth_key_and_dc_id  # old name: decryptor.get_auth_key_and_dc_id
from .utils import PROJECT_ROOT, CONFIG, read_txt_list

logger = logging.getLogger(__name__)


# --- Telethon configuration -------------------------------------------------


TELETHON_CONFIG: Dict[str, Any] = CONFIG.get("telethon", {})
API_ID: int = TELETHON_CONFIG.get("api_id")
API_HASH: str = TELETHON_CONFIG.get("api_hash")

TELEGRAM_CLIENT_META: Dict[str, Any] = CONFIG.get("telethon", {})
DEVICE_MODEL: str = TELEGRAM_CLIENT_META.get("telegram_device_model", "Python client")
SYSTEM_VERSION: str = TELEGRAM_CLIENT_META.get("telegram_system_version", "Unknown OS")
APP_VERSION: str = TELEGRAM_CLIENT_META.get("telegram_app_version", "1.0")


# --- Core session converter -------------------------------------------------


class Converter:
    """
    High-level helper for working with Telegram sessions and TData.

    Responsibilities:
      * Convert Telegram Desktop TData → Telethon session file.
      * Build Telethon client directly from raw auth key + DC.
      * Convert Android ``tgnet.dat`` + ``userconfing.xml`` → Telethon session or TData.
    """

    #: Mapping from Telegram DC id to IP address.
    DC_IPS = {
        1: "149.154.175.50",
        2: "149.154.167.51",
        3: "149.154.175.100",
        4: "149.154.167.91",
        5: "91.108.56.130",
    }

    def __init__(self, sessions_root: Optional[Path] = None) -> None:
        """
        :param sessions_root: Optional root directory for sessions.
                              Defaults to ``PROJECT_ROOT / "sessions"``.
        """
        self.sessions_root = (
            Path(sessions_root) if sessions_root is not None else PROJECT_ROOT / "sessions"
        )

    async def tdata_to_session(self, tdata_path: str | Path, session_folder: str | Path) -> bool:
        """
        Convert Telegram Desktop TData into a Telethon session file.

        Uses ``get_auth_key_and_dc_id`` to extract auth key, DC id and user id,
        then ``TGConvertor.SessionManager`` to write a Telethon ``.session`` file.

        :param tdata_path: Path to Telegram Desktop TData directory.
                           Usually points to a folder containing ``map*`` files.
        :param session_folder: Path to directory where ``.session`` will be stored.
        :return: True on success, False otherwise.
        """
        tdata_path = str(tdata_path)
        session_folder = Path(session_folder)
        session_folder.mkdir(parents=True, exist_ok=True)

        try:
            account_name = os.path.basename(os.path.dirname(tdata_path.rstrip("/\\")))
            session_path = session_folder / f"{account_name}.session"

            acc_data = get_auth_key_and_dc_id(tdata_path)
            auth_key_bytes = bytes.fromhex(acc_data["auth_key"])
            dc_id = acc_data["dc_id"]
            user_id = acc_data["user_id"]

            session_mgr = SessionManager(auth_key=auth_key_bytes, user_id=user_id, dc_id=dc_id)
            await session_mgr.to_telethon_file(str(session_path))

            print(f'✅ Converted TData "{account_name}" → {session_path}')
            logger.info('Converted TData "%s" to session %s', account_name, session_path)
            return True
        except Exception as e:
            print(f"[!] Failed to convert TData to session: {e}")
            logger.exception("Failed to convert TData to session from %s", tdata_path)
            return False

    def define_client_from_auth_key(
        self,
        auth_key_hex: str,
        dc_id: int,
        api_id: int,
        api_hash: str,
        save_session: bool = False,
        **kwargs: Any,
    ) -> TelegramClient:
        """
        Build a Telethon client from a raw auth key and DC id.

        This method does not require a phone number or password. It reconstructs
        the internal session object using the given auth key, DC id and API keys.

        :param auth_key_hex: Auth key as hex string.
        :param dc_id: Telegram DC id (1–5).
        :param api_id: Telegram API ID.
        :param api_hash: Telegram API hash.
        :param save_session: If True, create a persistent ``SQLiteSession`` on disk.
                             Otherwise use in-memory session.
        :param kwargs: Extra keyword arguments passed directly to ``TelegramClient``,
                       e.g. ``device_model``, ``system_version``, ``app_version``, ``proxy``, etc.
        :return: Configured ``TelegramClient`` instance (not yet connected).
        """
        auth_key_bytes = bytes.fromhex(auth_key_hex)

        if save_session:
            session_path: Path = kwargs.pop("session_path")
            session_path.parent.mkdir(parents=True, exist_ok=True)
            session = SQLiteSession(str(session_path.resolve()))
        else:
            session = MemorySession()

        session.set_dc(dc_id, self.DC_IPS[dc_id], 443)
        session.auth_key = AuthKey(auth_key_bytes)

        client = TelegramClient(session=session, api_id=api_id, api_hash=api_hash, **kwargs)
        return client

    def create_session_from_auth_key(
        self,
        session_path: str | Path,
        auth_key_hex: str,
        dc_id: int,
    ) -> Path:
        """
        Create a Telethon ``.session`` file directly from a raw auth key.

        This does *not* contact Telegram servers; it only writes the minimal
        data required for Telethon to reuse the auth key later.

        :param session_path: Target ``.session`` path.
        :param auth_key_hex: Auth key as hex string.
        :param dc_id: Telegram DC id (1–5).
        :return: Path to the created session file.
        """
        session_path = Path(session_path)
        session_path.parent.mkdir(parents=True, exist_ok=True)

        auth_key_bytes = bytes.fromhex(auth_key_hex)
        session = SQLiteSession(str(session_path))
        session.set_dc(dc_id, self.DC_IPS[dc_id], 443)
        session.auth_key = AuthKey(auth_key_bytes)
        session.save()

        logger.info("Session file created at %s from auth key (dc_id=%s)", session_path, dc_id)
        return session_path


# --- ADB-based helpers for Android tgnet.dat -------------------------------


def transfer_dat_session() -> None:
    """
    Copy ``tgnet.dat`` and ``userconfing.xml`` from an Android device to local ``sessions/dat``.

    The function assumes:
      * Telegram package: ``org.telegram.messenger``;
      * Device is connected via ADB;
      * Root access is available (uses ``su`` to read app-private data).

    Files are copied to ``/sdcard/`` on the device and then pulled to:

      ``PROJECT_ROOT / "sessions" / "dat" / {tgnet.dat,userconfing.xml}``
    """
    script_path = os.path.abspath(sys.argv[0])
    script_dir = os.path.dirname(script_path)

    dest_folder = os.path.join(script_dir, "sessions", "dat")
    os.makedirs(dest_folder, exist_ok=True)
    temp_dir = "/sdcard/"

    # Remote paths inside Android filesystem
    remote_tgnet_path = "/data/data/org.telegram.messenger/files/tgnet.dat"
    remote_config_path = "/data/data/org.telegram.messenger/shared_prefs/userconfing.xml"
    temp_tgnet_path = f"{temp_dir}tgnet.dat"
    temp_config_path = f"{temp_dir}userconfing.xml"

    # Local paths
    local_tgnet_path = os.path.join(dest_folder, "tgnet.dat")
    local_config_path = os.path.join(dest_folder, "userconfing.xml")

    process = subprocess.Popen(
        "adb shell",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=True,
    )

    commands = [
        "su",
        f"cp {remote_tgnet_path} {temp_tgnet_path}",
        f"cp {remote_config_path} {temp_config_path}",
        "exit",
        "exit",
    ]

    try:
        stdout, stderr = process.communicate("\n".join(commands), timeout=10)
        if stderr:
            print(f"ADB error: {stderr}")
            raise subprocess.CalledProcessError(process.returncode, commands, stderr=stderr)

        subprocess.run(f"adb pull {temp_tgnet_path} {local_tgnet_path}", check=True)
        subprocess.run(f"adb pull {temp_config_path} {local_config_path}", check=True)

        logger.info("Session files from device were transferred to %s", dest_folder)
    except subprocess.TimeoutExpired:
        print("ADB error: shell session timed out")
        process.kill()
        raise


def convert_dat_to_session(phone_number: str) -> bool:
    """
    Convert Android ``tgnet.dat`` + ``userconfing.xml`` to a Telethon session file.

    Expects that ``transfer_dat_session`` has already pulled the files to::

        ./sessions/dat/tgnet.dat
        ./sessions/dat/userconfing.xml

    :param phone_number: Phone number used only for naming the output file.
    :return: True on success, False otherwise.
    """
    script_path = os.path.abspath(sys.argv[0])
    script_dir = os.path.dirname(script_path)

    tgnet_path = os.path.join(script_dir, "sessions", "dat", "tgnet.dat")
    config_path = os.path.join(script_dir, "sessions", "dat", "userconfing.xml")

    today = datetime.now().strftime("%Y-%m-%d")
    converted_folder = os.path.join(script_dir, "sessions", "converted", today)
    os.makedirs(converted_folder, exist_ok=True)

    session_file_name = f"acc_{phone_number}.session"
    session_path = os.path.join(converted_folder, session_file_name)

    try:
        session = AndroidSession.from_tgnet(tgnet_path=tgnet_path, userconfig_path=config_path)
        session.to_telethon(session_path)
        logger.info("Session for acc_%s created in %s", phone_number, session_path)
        return True
    except Exception as e:
        logger.warning("Error creating session for acc_%s: %s", phone_number, e)
        return False


def convert_dat_to_tdata(phone_number: str) -> bool:
    """
    Convert Android ``tgnet.dat`` + ``userconfing.xml`` into Telegram Desktop TData.

    The resulting TData is stored under::

        ./sessions/converted/{yyyy-mm-dd}/acc_{phone_number}/

    :param phone_number: Phone number used only for naming the output folder.
    :return: True on success, False otherwise.
    """
    sessions_dir = os.path.join(os.path.dirname(__file__), "sessions")
    dat_dir = os.path.join(sessions_dir, "dat")
    tgnet_path = os.path.join(dat_dir, "tgnet.dat")
    config_path = os.path.join(dat_dir, "userconfing.xml")

    today = datetime.now().strftime("%Y-%m-%d")
    converted_base_dir = os.path.join(sessions_dir, "converted", today)
    os.makedirs(converted_base_dir, exist_ok=True)

    account_dir = os.path.join(converted_base_dir, f"acc_{phone_number}")
    os.makedirs(account_dir, exist_ok=True)

    try:
        session = AndroidSession.from_tgnet(tgnet_path=tgnet_path, userconfig_path=config_path)
        session.to_tdata(account_dir)
        logger.info("TData for account %s created in %s", phone_number, account_dir)
        return True
    except Exception as e:
        logger.error("Error creating TData for account %s: %s", phone_number, e)
        return False


# --- 2FA helper -------------------------------------------------------------


def set_2fa_safe(
    auth_key: str,
    dc_id: int,
    country: str,
    password: Optional[str],
    cur_password: Optional[str] = None,
    hint: str = "my password",
) -> None:
    """
    Safely set or reset Telegram 2FA (cloud password) using only auth key + DC.

    The function:
      * picks a random proxy from ``{country}_proxies.txt`` (one per line),
      * restores a Telethon client from ``auth_key`` + ``dc_id``,
      * connects and calls ``client.edit_2fa`` with proper error handling.

    :param auth_key: Auth key as hex string.
    :param dc_id: Telegram DC id.
    :param country: Country code used to choose proxy list, e.g. ``"USA"`` → ``USA_proxies.txt``.
    :param password: New cloud password to set. If ``None`` or empty, password will be removed.
    :param cur_password: Current password, if the account already has 2FA enabled.
    :param hint: Optional hint text for the new password.
    """
    # Load proxy configuration from `<country>_proxies.txt`
    proxy_list = read_txt_list(f"{country}_proxies.txt")
    proxy_str_splat = random.choice(proxy_list).strip().split(":")

    # Format Telethon proxy tuple:
    # ('socks5', host, port, rdns, username, password)
    proxy = (
        "socks5",
        proxy_str_splat[0],
        int(proxy_str_splat[1]),
        True,
        proxy_str_splat[2],
        proxy_str_splat[3],
    )

    converter = Converter()
    client = converter.define_client_from_auth_key(
        auth_key_hex=auth_key,
        dc_id=dc_id,
        api_id=API_ID,
        api_hash=API_HASH,
        system_version=SYSTEM_VERSION,
        device_model=DEVICE_MODEL,
        app_version=APP_VERSION,
        proxy=proxy,
    )

    try:
        if not client.is_connected():
            client.connect()

        # new_password=None → reset cloud password
        result = client.edit_2fa(
            current_password=cur_password,
            new_password=password,
            hint=hint,
        )

        if password:
            print("✅ Cloud password set successfully:", result)
        else:
            print("✅ Cloud password reset successfully:", result)

    except FloodError as e:
        if getattr(e, "seconds", None):
            hours = round(e.seconds / 3600, 2)
            print(f"⏳ FloodError: password change is temporarily locked. Wait {e.seconds} seconds (~{hours} h).")
        else:
            print("⏳ FloodError: method is frozen for this account (FROZEN_METHOD_INVALID).")

    except PasswordHashInvalidError:
        print("❌ Invalid current password (cur_password).")

    except SessionPasswordNeededError:
        print("⚠️ This account already has a password set. You must pass cur_password.")

    except Exception as e:
        print("⚠️ Unexpected error while changing 2FA password:", repr(e))

    finally:
        try:
            client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    # very small self-test stub (won't run anything dangerous by default)
    print("sessions.py module loaded. Use Converter and set_2fa_safe() from other scripts.")
