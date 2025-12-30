"""Tests for logging configuration module."""

import json
import logging
import pytest
from auto_reger.logging_config import (
    CorrelationFilter,
    JsonFormatter,
    LogContext,
    TextFormatter,
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
    setup_logging,
)


class TestCorrelationId:
    """Tests for correlation ID functions."""
    
    def test_generate_unique(self):
        """Test generated IDs are unique."""
        ids = [generate_correlation_id() for _ in range(100)]
        assert len(set(ids)) == 100
    
    def test_generate_format(self):
        """Test generated ID format."""
        cid = generate_correlation_id()
        assert len(cid) == 8
        assert all(c in "0123456789abcdef-" for c in cid)
    
    def test_set_and_get(self):
        """Test set and get correlation ID."""
        set_correlation_id("test-123")
        assert get_correlation_id() == "test-123"
    
    def test_default_empty(self):
        """Test default is empty string."""
        # Reset to default
        set_correlation_id("")
        assert get_correlation_id() == ""


class TestLogContext:
    """Tests for LogContext context manager."""
    
    def test_sets_correlation_id(self):
        """Test context manager sets correlation ID."""
        with LogContext("ctx-123") as cid:
            assert cid == "ctx-123"
            assert get_correlation_id() == "ctx-123"
    
    def test_generates_id_if_none(self):
        """Test generates ID if not provided."""
        with LogContext() as cid:
            assert len(cid) == 8
            assert get_correlation_id() == cid
    
    def test_restores_previous(self):
        """Test restores previous ID on exit."""
        set_correlation_id("original")
        
        with LogContext("temporary"):
            assert get_correlation_id() == "temporary"
        
        assert get_correlation_id() == "original"


class TestCorrelationFilter:
    """Tests for CorrelationFilter."""
    
    def test_adds_correlation_id(self):
        """Test filter adds correlation_id to record."""
        set_correlation_id("filter-test")
        
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        
        filter = CorrelationFilter()
        filter.filter(record)
        
        assert record.correlation_id == "filter-test"
    
    def test_default_dash(self):
        """Test default is dash when no correlation ID."""
        set_correlation_id("")
        
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        
        filter = CorrelationFilter()
        filter.filter(record)
        
        assert record.correlation_id == "-"


class TestJsonFormatter:
    """Tests for JsonFormatter."""
    
    def test_valid_json(self):
        """Test output is valid JSON."""
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=42,
            msg="test message", args=(), exc_info=None
        )
        record.correlation_id = "json-test"
        
        formatter = JsonFormatter()
        output = formatter.format(record)
        
        data = json.loads(output)
        assert data["level"] == "INFO"
        assert data["message"] == "test message"
        assert data["correlation_id"] == "json-test"
        assert data["line"] == 42
    
    def test_includes_timestamp(self):
        """Test includes ISO timestamp."""
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test", args=(), exc_info=None
        )
        record.correlation_id = "-"
        
        formatter = JsonFormatter()
        output = formatter.format(record)
        
        data = json.loads(output)
        assert "timestamp" in data
        assert data["timestamp"].endswith("Z")


class TestTextFormatter:
    """Tests for TextFormatter."""
    
    def test_includes_correlation_id(self):
        """Test output includes correlation ID."""
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=42,
            msg="test message", args=(), exc_info=None
        )
        record.correlation_id = "text-test"
        
        formatter = TextFormatter()
        output = formatter.format(record)
        
        assert "text-test" in output
        assert "INFO" in output
        assert "test message" in output
