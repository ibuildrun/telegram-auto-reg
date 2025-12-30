"""Tests for custom exceptions module."""

import pytest
from auto_reger.exceptions import (
    AutoRegerError,
    ConfigError,
    EmulatorError,
    ProxyError,
    SmsApiError,
    VpnError,
)


class TestAutoRegerError:
    """Tests for base AutoRegerError class."""
    
    def test_basic_message(self):
        """Test basic error message."""
        err = AutoRegerError("Something went wrong")
        assert str(err) == "Something went wrong"
        assert err.message == "Something went wrong"
        assert err.cause is None
    
    def test_with_cause(self):
        """Test error with cause exception."""
        cause = ValueError("Invalid value")
        err = AutoRegerError("Operation failed", cause=cause)
        assert "Caused by: ValueError: Invalid value" in str(err)
        assert err.cause is cause
    
    def test_with_context(self):
        """Test error with context fields."""
        err = AutoRegerError("Failed", provider="sms-activate", phone="+1234567890")
        assert "provider=sms-activate" in str(err)
        assert "phone=+1234567890" in str(err)
    
    def test_repr(self):
        """Test repr output."""
        err = AutoRegerError("Test", provider="test")
        assert "AutoRegerError" in repr(err)
        assert "Test" in repr(err)


class TestConfigError:
    """Tests for ConfigError class."""
    
    def test_with_field(self):
        """Test config error with field name."""
        err = ConfigError("Invalid value", field="api_key")
        assert err.field == "api_key"
        assert "api_key" in str(err)
    
    def test_with_expected_type(self):
        """Test config error with expected type."""
        err = ConfigError("Wrong type", field="port", expected_type="int")
        assert err.expected_type == "int"


class TestSmsApiError:
    """Tests for SmsApiError class."""
    
    def test_with_provider(self):
        """Test SMS error with provider."""
        err = SmsApiError("API failed", provider="sms-activate")
        assert err.provider == "sms-activate"
    
    def test_with_phone(self):
        """Test SMS error with phone number."""
        err = SmsApiError("SMS timeout", phone_number="+1234567890")
        assert err.phone_number == "+1234567890"


class TestEmulatorError:
    """Tests for EmulatorError class."""
    
    def test_with_device_id(self):
        """Test emulator error with device ID."""
        err = EmulatorError("Connection failed", device_id="127.0.0.1:5555")
        assert err.device_id == "127.0.0.1:5555"
    
    def test_with_operation(self):
        """Test emulator error with operation."""
        err = EmulatorError("Failed", operation="click")
        assert err.operation == "click"


class TestVpnError:
    """Tests for VpnError class."""
    
    def test_with_provider_and_location(self):
        """Test VPN error with provider and location."""
        err = VpnError("Connection failed", provider="ExpressVPN", location="USA")
        assert err.provider == "ExpressVPN"
        assert err.location == "USA"


class TestProxyError:
    """Tests for ProxyError class."""
    
    def test_with_host_and_port(self):
        """Test proxy error with host and port."""
        err = ProxyError("Connection refused", proxy_host="1.2.3.4", proxy_port=1080)
        assert err.proxy_host == "1.2.3.4"
        assert err.proxy_port == 1080
