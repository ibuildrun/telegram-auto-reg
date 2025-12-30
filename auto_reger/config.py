"""Configuration management with validation.

Provides typed configuration dataclasses and validation logic.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .exceptions import ConfigError


@dataclass
class PathConfig:
    """Paths to external tools."""
    chrome: str = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    expressvpn: str = r"C:\Program Files (x86)\ExpressVPN\expressvpn-ui\ExpressVPN.exe"
    adb: str = r"C:\Android\platform-tools\adb.exe"
    telegram_desktop: str = ""  # Auto-detected from %APPDATA%
    
    def __post_init__(self):
        if not self.telegram_desktop:
            appdata = os.environ.get("APPDATA", "")
            self.telegram_desktop = str(Path(appdata) / "Telegram Desktop" / "Telegram.exe")


@dataclass
class AdbConfig:
    """ADB and emulator settings."""
    device_type: str = "E"  # E = emulator, P = physical
    device_udid: str = "127.0.0.1:5555"
    appium_port: int = 4723
    adb_path: str = r"C:\Android\platform-tools\adb.exe"


@dataclass
class SmsConfig:
    """SMS provider settings."""
    provider: str = "sms-activate"
    api_key: str = ""
    api_key_file: str = ""  # Alternative: read key from file
    default_country: str = "russia"
    max_price: float = 50.0


@dataclass
class ProxyConfig:
    """Proxy settings."""
    enabled: bool = False
    proxy_file: str = ""
    proxy_type: str = "socks5"  # socks5, http, https


@dataclass
class VpnConfig:
    """VPN settings."""
    enabled: bool = True
    provider: str = "ExpressVPN"
    auto_rotate: bool = True
    locations: List[str] = field(default_factory=lambda: ["USA", "UK", "Germany"])


@dataclass
class TelethonConfig:
    """Telethon API settings."""
    api_id: int = 0
    api_hash: str = ""
    device_model: str = "Android"
    system_version: str = "10"
    app_version: str = "10.0.0"


@dataclass
class LoggingConfig:
    """Logging settings."""
    level: str = "INFO"
    file: str = "telegram_regger.log"
    json_format: bool = False
    module_levels: Dict[str, str] = field(default_factory=dict)


@dataclass
class AppConfig:
    """Main application configuration."""
    paths: PathConfig = field(default_factory=PathConfig)
    adb: AdbConfig = field(default_factory=AdbConfig)
    sms: SmsConfig = field(default_factory=SmsConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    vpn: VpnConfig = field(default_factory=VpnConfig)
    telethon: TelethonConfig = field(default_factory=TelethonConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


class ConfigValidator:
    """Configuration loader and validator."""
    
    ENV_VAR_PATTERN = re.compile(r"\$\{?(\w+)\}?")
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
    
    def load(self) -> AppConfig:
        """Load and validate configuration from file."""
        if not self.config_path.exists():
            raise ConfigError(
                f"Configuration file not found: {self.config_path}",
                field="config_path"
            )
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw_config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError("Invalid YAML syntax", cause=e)
        
        # Expand environment variables
        raw_config = self._expand_env_vars(raw_config)
        
        # Build config objects
        config = self._build_config(raw_config)
        
        # Validate
        self._validate(config)
        
        return config
    
    def _expand_env_vars(self, obj: Any) -> Any:
        """Recursively expand environment variables in strings."""
        if isinstance(obj, str):
            return self._expand_path(obj)
        elif isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        return obj
    
    def _expand_path(self, path: str) -> str:
        """Expand environment variables in path string."""
        def replace_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        
        expanded = self.ENV_VAR_PATTERN.sub(replace_var, path)
        return os.path.expandvars(expanded)
    
    def _build_config(self, raw: Dict[str, Any]) -> AppConfig:
        """Build typed config from raw dict."""
        return AppConfig(
            paths=PathConfig(**raw.get("paths", {})),
            adb=AdbConfig(**raw.get("adb", {})),
            sms=SmsConfig(**raw.get("sms", raw.get("sms_api", {}))),
            proxy=ProxyConfig(**raw.get("proxy", {})),
            vpn=VpnConfig(**raw.get("vpn", {})),
            telethon=TelethonConfig(**raw.get("telethon", {})),
            logging=LoggingConfig(**raw.get("logging", {})),
        )
    
    def _validate(self, config: AppConfig) -> None:
        """Validate configuration values."""
        # Validate ports
        self._validate_port(config.adb.appium_port, "adb.appium_port")
        
        # Validate API key
        if config.sms.api_key_file:
            self._validate_api_key_file(config.sms.api_key_file)
        
        # Validate proxy file
        if config.proxy.enabled and config.proxy.proxy_file:
            self._validate_file_exists(config.proxy.proxy_file, "proxy.proxy_file")
        
        # Validate Telethon credentials
        if config.telethon.api_id == 0:
            raise ConfigError(
                "Telethon API ID is required",
                field="telethon.api_id",
                expected_type="int > 0"
            )
        
        # Warn about missing paths (don't fail)
        self._warn_missing_path(config.paths.adb, "paths.adb")
        self._warn_missing_path(config.adb.adb_path, "adb.adb_path")
    
    def _validate_port(self, port: int, field_name: str) -> None:
        """Validate port is in valid range."""
        if not 1024 <= port <= 65535:
            raise ConfigError(
                f"Port must be between 1024 and 65535, got {port}",
                field=field_name,
                expected_type="int (1024-65535)"
            )
    
    def _validate_api_key_file(self, file_path: str) -> None:
        """Validate API key file exists and is not empty."""
        path = Path(file_path)
        if not path.exists():
            raise ConfigError(
                f"API key file not found: {file_path}",
                field="sms.api_key_file"
            )
        if path.stat().st_size == 0:
            raise ConfigError(
                f"API key file is empty: {file_path}",
                field="sms.api_key_file"
            )
    
    def _validate_file_exists(self, file_path: str, field_name: str) -> None:
        """Validate file exists."""
        if not Path(file_path).exists():
            raise ConfigError(
                f"File not found: {file_path}",
                field=field_name
            )
    
    def _warn_missing_path(self, path: str, field_name: str) -> None:
        """Log warning if path doesn't exist."""
        import logging
        if path and not Path(path).exists():
            logging.warning(f"Path not found for {field_name}: {path}")


def load_app_config(config_path: str = "config.yaml") -> AppConfig:
    """Convenience function to load configuration."""
    validator = ConfigValidator(config_path)
    return validator.load()
