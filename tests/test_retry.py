"""Tests for retry decorator module."""

import pytest
from unittest.mock import MagicMock, patch
from auto_reger.retry import retry, RetryContext


class TestRetryDecorator:
    """Tests for retry decorator."""
    
    def test_success_no_retry(self):
        """Test successful call without retry."""
        mock_func = MagicMock(return_value="success")
        
        @retry(max_retries=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_exception(self):
        """Test retry on exception."""
        mock_func = MagicMock(side_effect=[ValueError("fail"), ValueError("fail"), "success"])
        
        @retry(max_retries=3, delay_seconds=0.01, exceptions_to_retry=(ValueError,))
        def test_func():
            return mock_func()
        
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_exhausted_retries(self):
        """Test all retries exhausted."""
        mock_func = MagicMock(side_effect=ValueError("always fail"))
        
        @retry(max_retries=3, delay_seconds=0.01, exceptions_to_retry=(ValueError,))
        def test_func():
            return mock_func()
        
        with pytest.raises(ValueError, match="always fail"):
            test_func()
        
        assert mock_func.call_count == 3
    
    def test_non_retryable_exception(self):
        """Test non-retryable exception raises immediately."""
        mock_func = MagicMock(side_effect=TypeError("wrong type"))
        
        @retry(max_retries=3, delay_seconds=0.01, exceptions_to_retry=(ValueError,))
        def test_func():
            return mock_func()
        
        with pytest.raises(TypeError, match="wrong type"):
            test_func()
        
        assert mock_func.call_count == 1
    
    def test_backoff_multiplier(self):
        """Test exponential backoff is applied."""
        delays = []
        
        def mock_sleep(seconds):
            delays.append(seconds)
        
        mock_func = MagicMock(side_effect=[ValueError(), ValueError(), "success"])
        
        @retry(max_retries=3, delay_seconds=1.0, backoff_multiplier=2.0, exceptions_to_retry=(ValueError,))
        def test_func():
            return mock_func()
        
        with patch("auto_reger.retry.time.sleep", mock_sleep):
            test_func()
        
        assert len(delays) == 2
        assert delays[0] == 1.0
        assert delays[1] == 2.0


class TestRetryContext:
    """Tests for RetryContext class."""
    
    def test_should_retry_true(self):
        """Test should_retry returns True when retries available."""
        ctx = RetryContext(max_retries=3, delay_seconds=0.01)
        
        with patch("auto_reger.retry.time.sleep"):
            assert ctx.should_retry(ValueError("test")) is True
            assert ctx.attempt == 1
    
    def test_should_retry_false_exhausted(self):
        """Test should_retry returns False when exhausted."""
        ctx = RetryContext(max_retries=2, delay_seconds=0.01)
        
        with patch("auto_reger.retry.time.sleep"):
            ctx.should_retry(ValueError("test"))
            ctx.should_retry(ValueError("test"))
            assert ctx.should_retry(ValueError("test")) is False
    
    def test_should_retry_false_wrong_exception(self):
        """Test should_retry returns False for wrong exception type."""
        ctx = RetryContext(max_retries=3, exceptions_to_retry=(ValueError,))
        
        assert ctx.should_retry(TypeError("test")) is False
    
    def test_reset(self):
        """Test reset clears state."""
        ctx = RetryContext(max_retries=3, delay_seconds=1.0)
        ctx.attempt = 2
        ctx.current_delay = 4.0
        ctx.last_exception = ValueError("test")
        
        ctx.reset()
        
        assert ctx.attempt == 0
        assert ctx.current_delay == 1.0
        assert ctx.last_exception is None
