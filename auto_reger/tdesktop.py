import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from tdesktop_decrypter.decrypter import TdataReader, NoKeyFileException
from tdesktop_decrypter.cli import display_setting_value

from .utils import write_json, LOG_FILE

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
    encoding="utf-8",
)


def display_json(parsed_tdata) -> Dict[str, Any]:
    """
    Convert parsed TData object into a JSON-serializable structure.

    The output format is:

    {
        "accounts": [
            {
                "index": int,
                "user_id": int,
                "main_dc_id": int,
                "dc_auth_keys": { dc_id: auth_key_hex, ... }
            },
            ...
        ],
        "settings": { ... } or None
    }

    :param parsed_tdata: Parsed TData object from `TdataReader.read()`.
    :return: Python dict ready to be dumped as JSON.
    """
    accounts: List[Dict[str, Any]] = [
        {
            "index": account.index,
            "user_id": account.mtp_data.user_id,
            "main_dc_id": account.mtp_data.current_dc_id,
            "dc_auth_keys": {
                dc_id: key.hex().lower()
                for dc_id, key in account.mtp_data.keys.items()
            },
        }
        for account in parsed_tdata.accounts.values()
    ]

    if parsed_tdata.settings is None:
        settings = None
    else:
        settings = {
            str(k): display_setting_value(v)
            for k, v in parsed_tdata.settings.items()
        }

    obj: Dict[str, Any] = {
        "accounts": accounts,
        "settings": settings,
    }
    return obj


def get_auth_key_and_dc_id(
    tdata_path: str | Path,
    passcode: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Extract `dc_id`, `auth_key` and `user_id` for the main account from TData.

    This helper:
      * reads Telegram Desktop TData from `tdata_path`,
      * converts it into JSON-like structure via `display_json`,
      * looks for the account with `index == 0` (main account).

    :param tdata_path: Path to TData directory (with `map*` files).
    :param passcode: Optional local passcode, if TData is protected.
    :return: Dict with keys `dc_id`, `auth_key` (hex str), `user_id`,
             or None if nothing was found.
    """
    tdata_path = str(tdata_path)

    reader = TdataReader(tdata_path)
    try:
        parsed_data = reader.read(passcode)
        json_data = display_json(parsed_data)

        for account in json_data["accounts"]:
            if account["index"] == 0:
                dc_id = account["main_dc_id"]
                auth_key = account["dc_auth_keys"][dc_id]
                user_id = account["user_id"]
                return {
                    "dc_id": dc_id,
                    "auth_key": auth_key,
                    "user_id": user_id,
                }

    except NoKeyFileException as exc:
        print(f"No key file was found. Is the tdata path correct?: {exc}")
        logging.warning("NoKeyFileException for tdata_path=%s: %s", tdata_path, exc)
    except Exception as exc:
        print(f"Failed to read TData from {tdata_path}: {exc}")
        logging.exception("Failed to read TData from %s", tdata_path)

    return None


def decrypt_folder_with_accounts(
    folder_path: str | Path,
    country: str,
) -> Path:
    """
    Walk through a folder of per-account TData directories and extract auth data.

    Expected structure:

        folder_path/
            acc_1/
                tdata/  <- Telegram Desktop TData directory
            acc_2/
                tdata/
            ...

    For each TData folder, the function tries to read `dc_id`, `auth_key`,
    `user_id` and accumulates them into a list. At the end it saves:

      * `{last_folder_name}_{country}.json` with accounts data
      * `errors.json` (if there were folders that could not be decoded)

    :param folder_path: Directory containing account subfolders.
    :param country: Country code used only in the output file name.
    :return: Full path to the main JSON file with account data.
    """
    folder_path = str(folder_path)
    accounts_folder_list = os.listdir(folder_path)
    last_folder = os.path.basename(folder_path.rstrip("/\\"))

    items_data: List[Dict[str, Any]] = []
    errors: List[str] = []

    for acc_folder in accounts_folder_list:
        acc_dir = os.path.join(folder_path, acc_folder)
        if not os.path.isdir(acc_dir):
            continue

        tdata_path = os.path.join(acc_dir, "tdata")
        if not os.path.isdir(tdata_path):
            errors.append(acc_folder)
            print(f"Account folder {acc_folder} has no 'tdata' directory")
            continue

        item_data = get_auth_key_and_dc_id(tdata_path)
        if item_data:
            items_data.append(item_data)
            continue

        errors.append(acc_folder)
        print(
            f"No valid auth data found for account folder {acc_folder} "
            f"(path={tdata_path})"
        )

    print(f"Decrypted {len(items_data)} accounts from {folder_path}")
    logging.info("Decrypted %s accounts from %s", len(items_data), folder_path)

    file_name = f"{last_folder}_{country}.json"
    main_json_path = os.path.join(folder_path, file_name)
    write_json(items_data, main_json_path)

    if errors:
        errors_path = os.path.join(folder_path, "errors.json")
        write_json(errors, errors_path)
        logging.info(
            "Errors while decrypting accounts from %s written to %s",
            folder_path,
            errors_path,
        )

    return Path(main_json_path)


if __name__ == "__main__":
    # Minimal manual test stub (no external side effects).
    print(
        "This module provides helpers for Telegram Desktop TData:\n"
        " - get_auth_key_and_dc_id(tdata_path)\n"
        " - decrypt_folder_with_accounts(folder_path, country)\n"
        "Use them from other scripts in the project."
    )
