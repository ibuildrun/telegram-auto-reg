"""Retry decorator for unstable operations.

Provides automatic retry with exponential backoff for transient failures.
"""

import functools
import logging
import time
from typing import Callable, Tuple, Type, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry(
    max_retries: int = 3,
    delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    exceptions_to_retry: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for automatic retry with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        delay_seconds: Initial delay between retries in seconds (default: 1.0)
        backoff_multiplier: Multiplier for exponential backoff (default: 2.0)
        exceptions_to_retry: Tuple of exception types to retry on (default: all)
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @retry(max_retries=3, delay_seconds=1, exceptions_to_retry=(ConnectionError,))
        def fetch_data():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception = Exception("No attempts made")
            current_delay = delay_seconds
            
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions_to_retry as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Retry {attempt}/{max_retries} for {func.__name__}: "
                            f"{type(e).__name__}: {e}. Waiting {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_multiplier
                    else:
                        logger.error(
                            f"All {max_retries} retries exhausted for {func.__name__}: "
                            f"{type(e).__name__}: {e}"
                        )
                except Exception as e:
                    # Non-retryable exception - re-raise immediately
                    logger.error(
                        f"Non-retryable exception in {func.__name__}: "
                        f"{type(e).__name__}: {e}"
                    )
                    raise
            
            raise last_exception
        
        return wrapper
    return decorator


class RetryContext:
    """Context manager for retry logic with state tracking."""
    
    def __init__(
        self,
        max_retries: int = 3,
        delay_seconds: float = 1.0,
        backoff_multiplier: float = 2.0,
        exceptions_to_retry: Tuple[Type[Exception], ...] = (Exception,),
    ):
        self.max_retries = max_retries
        self.delay_seconds = delay_seconds
        self.backoff_multiplier = backoff_multiplier
        self.exceptions_to_retry = exceptions_to_retry
        self.attempt = 0
        self.current_delay = delay_seconds
        self.last_exception: Exception | None = None
    
    def should_retry(self, exception: Exception) -> bool:
        """Check if should retry after exception."""
        if not isinstance(exception, self.exceptions_to_retry):
            return False
        
        self.last_exception = exception
        self.attempt += 1
        
        if self.attempt >= self.max_retries:
            return False
        
        logger.warning(
            f"Retry {self.attempt}/{self.max_retries}: "
            f"{type(exception).__name__}: {exception}. "
            f"Waiting {self.current_delay:.1f}s..."
        )
        time.sleep(self.current_delay)
        self.current_delay *= self.backoff_multiplier
        return True
    
    def reset(self) -> None:
        """Reset retry state."""
        self.attempt = 0
        self.current_delay = self.delay_seconds
        self.last_exception = None
