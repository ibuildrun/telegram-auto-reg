"""Structured logging configuration with correlation ID support.

Provides JSON and text formatters with correlation ID tracking.
"""

import json
import logging
import sys
import traceback
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variable for correlation ID (thread-safe)
_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def generate_correlation_id() -> str:
    """Generate a new unique correlation ID."""
    return str(uuid.uuid4())[:8]


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current context."""
    _correlation_id.set(correlation_id)


def get_correlation_id() -> str:
    """Get correlation ID for current context."""
    return _correlation_id.get()


class CorrelationFilter(logging.Filter):
    """Filter that adds correlation_id to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "-"
        return True


class JsonFormatter(logging.Formatter):
    """JSON log formatter with all required fields."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "-"),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "correlation_id", "message"
            ):
                log_data[key] = value
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter with correlation ID."""
    
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(correlation_id)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging(
    log_file: Optional[str] = None,
    log_level: str = "INFO",
    json_format: bool = False,
    module_levels: Optional[Dict[str, str]] = None,
) -> None:
    """Configure logging for the application.
    
    Args:
        log_file: Path to log file (None for stdout only)
        log_level: Default log level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON format instead of text
        module_levels: Dict of module name -> log level overrides
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = JsonFormatter() if json_format else TextFormatter()
    
    # Create correlation filter
    correlation_filter = CorrelationFilter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    console_handler.addFilter(correlation_filter)
    root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(formatter)
        file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)
    
    # Per-module log levels
    if module_levels:
        for module_name, level in module_levels.items():
            module_logger = logging.getLogger(module_name)
            module_logger.setLevel(getattr(logging, level.upper()))
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("appium").setLevel(logging.WARNING)


class LogContext:
    """Context manager for setting correlation ID during a block."""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or generate_correlation_id()
        self._token = None
    
    def __enter__(self) -> str:
        self._token = _correlation_id.set(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, *args) -> None:
        if self._token:
            _correlation_id.reset(self._token)
