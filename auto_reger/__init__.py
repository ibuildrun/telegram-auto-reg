"""Auto-Regger - Telegram registration automation toolkit.

Core modules:
- config: Configuration management with validation
- exceptions: Custom exception classes
- retry: Retry decorator for unstable operations
- logging_config: Structured logging with correlation ID
- sms_api: SMS provider integration
- adb: Android Debug Bridge helpers
- sessions: Session conversion utilities
- tdesktop: Telegram Desktop TData handling
"""

from .config import AppConfig, ConfigValidator, load_app_config
from .exceptions import (
    AutoRegerError,
    ConfigError,
    EmulatorError,
    ProxyError,
    RegistrationError,
    SessionError,
    SmsApiError,
    VpnError,
)
from .logging_config import (
    LogContext,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
    setup_logging,
)
from .retry import RetryContext, retry

__all__ = [
    # Config
    "AppConfig",
    "ConfigValidator",
    "load_app_config",
    # Exceptions
    "AutoRegerError",
    "ConfigError",
    "EmulatorError",
    "ProxyError",
    "RegistrationError",
    "SessionError",
    "SmsApiError",
    "VpnError",
    # Logging
    "LogContext",
    "generate_correlation_id",
    "get_correlation_id",
    "set_correlation_id",
    "setup_logging",
    # Retry
    "RetryContext",
    "retry",
]

__version__ = "1.0.0"
