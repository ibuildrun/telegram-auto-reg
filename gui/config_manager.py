"""Configuration manager for GUI settings."""

import os
import yaml
from pathlib import Path


CONFIG_FILE = Path(__file__).parent.parent / "config.yaml"

DEFAULT_CONFIG = {
    "sms_api": {
        "provider": "sms-activate",
        "api_key": "",
    },
    "telethon": {
        "api_id": "",
        "api_hash": "",
    },
    "adb": {
        "device_type": "E",
        "device_udid": "127.0.0.1:5555",
        "appium_port": 4723,
        "adb_path": "C:\\Android\\platform-tools\\adb.exe",
    },
    "vpn": {
        "enabled": True,
        "provider": "ExpressVPN",
    },
    "proxy": {
        "enabled": False,
        "type": "SOCKS5",
        "host": "",
        "port": "",
        "username": "",
        "password": "",
    },
}


def load_config() -> dict:
    """Load configuration from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                # Merge with defaults
                return _merge_config(DEFAULT_CONFIG, config)
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> bool:
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def _merge_config(default: dict, loaded: dict) -> dict:
    """Merge loaded config with defaults."""
    result = default.copy()
    for key, value in loaded.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_config(result[key], value)
        else:
            result[key] = value
    return result
