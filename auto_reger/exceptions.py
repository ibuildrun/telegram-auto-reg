"""Custom exceptions for Telegram Auto-Regger.

Provides specific exception classes for each component with context information.
"""

from typing import Any, Optional


class AutoRegerError(Exception):
    """Base exception for all Auto-Regger errors."""
    
    def __init__(self, message: str, cause: Optional[Exception] = None, **context: Any):
        self.message = message
        self.cause = cause
        self.context = context
        
        # Build full message with cause
        full_message = message
        if cause:
            full_message = f"{message} | Caused by: {type(cause).__name__}: {cause}"
        if context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in context.items())
            full_message = f"{full_message} [{ctx_str}]"
        
        super().__init__(full_message)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, cause={self.cause!r}, context={self.context!r})"


class ConfigError(AutoRegerError):
    """Configuration validation or loading error."""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 expected_type: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(
            message, cause=cause,
            field=field, expected_type=expected_type
        )
        self.field = field
        self.expected_type = expected_type


class SmsApiError(AutoRegerError):
    """SMS provider API error."""
    
    def __init__(self, message: str, provider: Optional[str] = None,
                 phone_number: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(
            message, cause=cause,
            provider=provider, phone_number=phone_number
        )
        self.provider = provider
        self.phone_number = phone_number


class EmulatorError(AutoRegerError):
    """Appium/ADB emulator error."""
    
    def __init__(self, message: str, device_id: Optional[str] = None,
                 operation: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(
            message, cause=cause,
            device_id=device_id, operation=operation
        )
        self.device_id = device_id
        self.operation = operation


class VpnError(AutoRegerError):
    """VPN automation error."""
    
    def __init__(self, message: str, provider: Optional[str] = None,
                 location: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(
            message, cause=cause,
            provider=provider, location=location
        )
        self.provider = provider
        self.location = location


class ProxyError(AutoRegerError):
    """Proxy connection error."""
    
    def __init__(self, message: str, proxy_host: Optional[str] = None,
                 proxy_port: Optional[int] = None, cause: Optional[Exception] = None):
        super().__init__(
            message, cause=cause,
            proxy_host=proxy_host, proxy_port=proxy_port
        )
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port


class SessionError(AutoRegerError):
    """Session conversion or management error."""
    
    def __init__(self, message: str, session_type: Optional[str] = None,
                 phone_number: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(
            message, cause=cause,
            session_type=session_type, phone_number=phone_number
        )
        self.session_type = session_type
        self.phone_number = phone_number


class RegistrationError(AutoRegerError):
    """Registration flow error."""
    
    def __init__(self, message: str, step: Optional[str] = None,
                 phone_number: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(
            message, cause=cause,
            step=step, phone_number=phone_number
        )
        self.step = step
        self.phone_number = phone_number
