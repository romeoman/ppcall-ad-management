"""
Comprehensive tests for the error handling and recovery system.
"""

import pytest
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from src.utils.error_handler import (
    PPCError,
    APIError,
    RateLimitError,
    ValidationError,
    ErrorSeverity,
    ErrorCategory,
    RetryConfig,
    retry_with_backoff,
    ErrorLogger,
    ProgressTracker,
    handle_api_response
)


class TestPPCError:
    """Test custom error classes."""
    
    def test_ppc_error_initialization(self):
        """Test PPCError initialization with all parameters."""
        context = {"key": "value", "request_id": "123"}
        error = PPCError(
            "Test error",
            category=ErrorCategory.API_ERROR,
            severity=ErrorSeverity.HIGH,
            context=context,
            retry_after=30
        )
        
        assert str(error) == "Test error"
        assert error.category == ErrorCategory.API_ERROR
        assert error.severity == ErrorSeverity.HIGH
        assert error.context == context
        assert error.retry_after == 30
        assert isinstance(error.timestamp, datetime)
    
    def test_error_to_dict(self):
        """Test converting error to dictionary."""
        error = PPCError(
            "Test error",
            category=ErrorCategory.NETWORK_ERROR,
            severity=ErrorSeverity.MEDIUM
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["message"] == "Test error"
        assert error_dict["category"] == "network_error"
        assert error_dict["severity"] == "medium"
        assert "timestamp" in error_dict
    
    def test_api_error(self):
        """Test APIError subclass."""
        error = APIError("API failed", severity=ErrorSeverity.HIGH)
        
        assert error.category == ErrorCategory.API_ERROR
        assert str(error) == "API failed"
        assert error.severity == ErrorSeverity.HIGH
    
    def test_rate_limit_error(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError("Rate limit exceeded", retry_after=120)
        
        assert error.category == ErrorCategory.RATE_LIMIT
        assert error.retry_after == 120
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError("Invalid data format")
        
        assert error.category == ErrorCategory.VALIDATION_ERROR
        assert str(error) == "Invalid data format"


class TestRetryConfig:
    """Test retry configuration."""
    
    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
    
    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=0.5,
            max_delay=30.0,
            exponential_base=3.0,
            jitter=False
        )
        
        assert config.max_attempts == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
    
    def test_calculate_delay_without_jitter(self):
        """Test delay calculation without jitter."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            jitter=False
        )
        
        assert config.calculate_delay(1) == 1.0  # 1 * 2^0
        assert config.calculate_delay(2) == 2.0  # 1 * 2^1
        assert config.calculate_delay(3) == 4.0  # 1 * 2^2
        assert config.calculate_delay(4) == 8.0  # 1 * 2^3
        assert config.calculate_delay(5) == 10.0  # capped at max_delay
    
    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=True
        )
        
        delay = config.calculate_delay(2)
        # With jitter, delay should be between 1.0 and 3.0 (base delay is 2.0 with jitter factor)
        # Jitter multiplies by (0.5 + random()), so range is 0.5 * 2.0 to 1.5 * 2.0
        assert 1.0 <= delay <= 3.0


class TestRetryDecorator:
    """Test retry_with_backoff decorator."""
    
    def test_sync_function_success_first_try(self):
        """Test sync function succeeds on first try."""
        mock_func = Mock(return_value="success")
        
        @retry_with_backoff(RetryConfig(max_attempts=3))
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_sync_function_retry_and_succeed(self):
        """Test sync function fails then succeeds."""
        mock_func = Mock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        
        @retry_with_backoff(
            RetryConfig(max_attempts=3, initial_delay=0.01)
        )
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_sync_function_max_retries_exceeded(self):
        """Test sync function fails after max retries."""
        mock_func = Mock(side_effect=Exception("persistent error"))
        
        @retry_with_backoff(
            RetryConfig(max_attempts=3, initial_delay=0.01)
        )
        def test_func():
            return mock_func()
        
        with pytest.raises(Exception, match="persistent error"):
            test_func()
        
        assert mock_func.call_count == 3
    
    @pytest.mark.asyncio
    async def test_async_function_success_first_try(self):
        """Test async function succeeds on first try."""
        mock_func = Mock(return_value="success")
        
        @retry_with_backoff(RetryConfig(max_attempts=3))
        async def test_func():
            return mock_func()
        
        result = await test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_async_function_retry_and_succeed(self):
        """Test async function fails then succeeds."""
        mock_func = Mock(side_effect=[Exception("fail"), "success"])
        
        @retry_with_backoff(
            RetryConfig(max_attempts=3, initial_delay=0.01)
        )
        async def test_func():
            return mock_func()
        
        result = await test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_retry_with_specific_exceptions(self):
        """Test retry only on specific exceptions."""
        mock_func = Mock(side_effect=[ValueError("retry this"), "success"])
        
        @retry_with_backoff(
            RetryConfig(max_attempts=3, initial_delay=0.01),
            exceptions=(ValueError,)
        )
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_retry_callback(self):
        """Test retry callback is called."""
        callback = Mock()
        mock_func = Mock(side_effect=[Exception("fail"), "success"])
        
        @retry_with_backoff(
            RetryConfig(max_attempts=3, initial_delay=0.01),
            on_retry=callback
        )
        def test_func():
            return mock_func()
        
        test_func()
        
        assert callback.call_count == 1
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0] == 1  # attempt number
        assert isinstance(args[1], float)  # delay
        assert isinstance(args[2], Exception)  # exception


class TestErrorLogger:
    """Test error logging functionality."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary directory for logs."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_error_logger_initialization(self, temp_log_dir):
        """Test ErrorLogger initialization."""
        logger = ErrorLogger(log_dir=temp_log_dir)
        
        assert logger.log_dir == temp_log_dir
        assert logger.log_dir.exists()
        assert logger.error_file.name.startswith("errors_")
        assert logger.error_file.suffix == ".json"
    
    def test_log_standard_error(self, temp_log_dir):
        """Test logging standard exception."""
        logger = ErrorLogger(log_dir=temp_log_dir)
        
        error = ValueError("Test error")
        context = {"user_id": "123", "action": "test"}
        
        logger.log_error(error, context=context, user_message="Something went wrong")
        
        # Check log file was created and contains error
        assert logger.error_file.exists()
        
        with open(logger.error_file, 'r') as f:
            log_data = json.loads(f.readline())
        
        assert log_data["type"] == "ValueError"
        assert log_data["message"] == "Test error"
        assert log_data["context"] == context
        assert log_data["user_message"] == "Something went wrong"
        assert "timestamp" in log_data
    
    def test_log_ppc_error(self, temp_log_dir):
        """Test logging PPCError with severity."""
        logger = ErrorLogger(log_dir=temp_log_dir)
        
        error = APIError(
            "API request failed",
            severity=ErrorSeverity.HIGH,
            context={"endpoint": "/api/test"}
        )
        
        logger.log_error(error)
        
        with open(logger.error_file, 'r') as f:
            log_data = json.loads(f.readline())
        
        assert log_data["type"] == "APIError"
        assert log_data["category"] == "api_error"
        assert log_data["severity"] == "high"
        assert log_data["context"]["endpoint"] == "/api/test"
    
    def test_get_recent_errors(self, temp_log_dir):
        """Test retrieving recent errors."""
        logger = ErrorLogger(log_dir=temp_log_dir)
        
        # Log some errors
        logger.log_error(ValueError("Error 1"))
        time.sleep(0.1)
        logger.log_error(ValueError("Error 2"))
        time.sleep(0.1)
        logger.log_error(ValueError("Error 3"))
        
        # Get recent errors
        recent_errors = logger.get_recent_errors(hours=1)
        
        assert len(recent_errors) == 3
        assert recent_errors[0]["message"] == "Error 1"
        assert recent_errors[1]["message"] == "Error 2"
        assert recent_errors[2]["message"] == "Error 3"
    
    def test_get_recent_errors_time_filter(self, temp_log_dir):
        """Test time filtering for recent errors."""
        logger = ErrorLogger(log_dir=temp_log_dir)
        
        # Create an old error (mock timestamp)
        old_error = {
            "timestamp": (datetime.now() - timedelta(hours=25)).isoformat(),
            "message": "Old error"
        }
        
        with open(logger.error_file, 'w') as f:
            json.dump(old_error, f)
            f.write('\n')
        
        # Log a recent error
        logger.log_error(ValueError("Recent error"))
        
        # Get errors from last 24 hours
        recent_errors = logger.get_recent_errors(hours=24)
        
        assert len(recent_errors) == 1
        assert recent_errors[0]["message"] == "Recent error"


class TestProgressTracker:
    """Test progress tracking and resume functionality."""
    
    @pytest.fixture
    def temp_state_dir(self):
        """Create temporary directory for state files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_progress_tracker_initialization(self, temp_state_dir):
        """Test ProgressTracker initialization."""
        tracker = ProgressTracker(state_dir=temp_state_dir)
        
        assert tracker.state_dir == temp_state_dir
        assert tracker.state_dir.exists()
    
    def test_save_progress(self, temp_state_dir):
        """Test saving progress state."""
        tracker = ProgressTracker(state_dir=temp_state_dir)
        
        progress_data = {
            "processed_keywords": ["keyword1", "keyword2"],
            "current_batch": 2,
            "last_api_call": "2024-01-01T12:00:00"
        }
        
        tracker.save_progress(
            task_id="test_task",
            progress=progress_data,
            total_items=100,
            completed_items=25
        )
        
        state_file = temp_state_dir / "test_task.json"
        assert state_file.exists()
        
        with open(state_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["task_id"] == "test_task"
        assert saved_data["progress"] == progress_data
        assert saved_data["total_items"] == 100
        assert saved_data["completed_items"] == 25
        assert saved_data["percentage"] == 25.0
    
    def test_load_progress(self, temp_state_dir):
        """Test loading saved progress."""
        tracker = ProgressTracker(state_dir=temp_state_dir)
        
        # Save progress first
        progress_data = {"current": "state"}
        tracker.save_progress(
            task_id="test_task",
            progress=progress_data,
            total_items=50,
            completed_items=10
        )
        
        # Load progress
        loaded = tracker.load_progress("test_task")
        
        assert loaded is not None
        assert loaded["task_id"] == "test_task"
        assert loaded["progress"] == progress_data
        assert loaded["total_items"] == 50
        assert loaded["completed_items"] == 10
    
    def test_load_nonexistent_progress(self, temp_state_dir):
        """Test loading progress for non-existent task."""
        tracker = ProgressTracker(state_dir=temp_state_dir)
        
        loaded = tracker.load_progress("nonexistent_task")
        
        assert loaded is None
    
    def test_clear_progress(self, temp_state_dir):
        """Test clearing saved progress."""
        tracker = ProgressTracker(state_dir=temp_state_dir)
        
        # Save progress
        tracker.save_progress(
            task_id="test_task",
            progress={},
            total_items=10,
            completed_items=5
        )
        
        state_file = temp_state_dir / "test_task.json"
        assert state_file.exists()
        
        # Clear progress
        tracker.clear_progress("test_task")
        
        assert not state_file.exists()
    
    def test_list_resumable_tasks(self, temp_state_dir):
        """Test listing all resumable tasks."""
        tracker = ProgressTracker(state_dir=temp_state_dir)
        
        # Save multiple task progress
        tracker.save_progress("task1", {}, 100, 50)
        time.sleep(0.1)
        tracker.save_progress("task2", {}, 200, 150)
        time.sleep(0.1)
        tracker.save_progress("task3", {}, 50, 25)
        
        tasks = tracker.list_resumable_tasks()
        
        assert len(tasks) == 3
        # Should be sorted by timestamp (newest first)
        assert tasks[0]["task_id"] == "task3"
        assert tasks[1]["task_id"] == "task2"
        assert tasks[2]["task_id"] == "task1"
        
        # Check task details
        assert tasks[0]["percentage"] == 50.0
        assert tasks[0]["completed"] == 25
        assert tasks[0]["total"] == 50


class TestHandleApiResponse:
    """Test API response handling."""
    
    def test_handle_successful_response(self):
        """Test handling successful API response."""
        response = {
            "data": {
                "results": ["item1", "item2"],
                "count": 2
            }
        }
        
        result = handle_api_response(response)
        
        assert result == response["data"]
        assert result["results"] == ["item1", "item2"]
        assert result["count"] == 2
    
    def test_handle_response_without_data_wrapper(self):
        """Test handling response without 'data' wrapper."""
        response = {
            "results": ["item1", "item2"],
            "count": 2
        }
        
        result = handle_api_response(response)
        
        assert result == response
        assert result["results"] == ["item1", "item2"]
    
    def test_handle_error_response_with_raise(self):
        """Test handling error response with exception raising."""
        response = {
            "error": {
                "message": "Invalid API key",
                "code": "AUTH_ERROR"
            }
        }
        
        with pytest.raises(APIError, match="Invalid API key"):
            handle_api_response(response, raise_on_error=True)
    
    def test_handle_error_response_without_raise(self):
        """Test handling error response without raising."""
        response = {
            "error": {
                "message": "Invalid request",
                "code": "VALIDATION_ERROR"
            }
        }
        
        result = handle_api_response(response, raise_on_error=False)
        
        assert result == {}
    
    def test_handle_rate_limit_error(self):
        """Test handling rate limit error."""
        response = {
            "error": {
                "message": "Rate limit exceeded",
                "code": "RATE_LIMIT",
                "retry_after": 120
            }
        }
        
        with pytest.raises(RateLimitError) as exc_info:
            handle_api_response(response)
        
        assert exc_info.value.retry_after == 120
        assert "Rate limit exceeded" in str(exc_info.value)