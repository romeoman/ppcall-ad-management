"""
Comprehensive error handling module with retry logic, exponential backoff,
and recovery mechanisms for the PPC Campaign Manager.
"""

import asyncio
import logging
import time
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from functools import wraps
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels for categorizing errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for better organization."""
    API_ERROR = "api_error"
    RATE_LIMIT = "rate_limit"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    FILE_ERROR = "file_error"
    PARSING_ERROR = "parsing_error"
    AUTH_ERROR = "auth_error"
    UNKNOWN = "unknown"


class PPCError(Exception):
    """Base exception class for PPC Campaign Manager."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.retry_after = retry_after
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            "message": str(self),
            "category": self.category.value,
            "severity": self.severity.value,
            "context": self.context,
            "retry_after": self.retry_after,
            "timestamp": self.timestamp.isoformat()
        }


class APIError(PPCError):
    """API-related errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.API_ERROR, **kwargs)


class RateLimitError(PPCError):
    """Rate limit errors with retry information."""
    def __init__(self, message: str, retry_after: int = 60, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.RATE_LIMIT,
            retry_after=retry_after,
            **kwargs
        )


class ValidationError(PPCError):
    """Data validation errors."""
    def __init__(self, message: str, **kwargs):
        super().__init__(message, category=ErrorCategory.VALIDATION_ERROR, **kwargs)


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number with exponential backoff."""
        delay = min(
            self.initial_delay * (self.exponential_base ** (attempt - 1)),
            self.max_delay
        )
        
        if self.jitter:
            # Add random jitter to prevent thundering herd
            import random
            delay = delay * (0.5 + random.random())
        
        return delay


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        config: Retry configuration
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )
                        raise
                    
                    delay = config.calculate_delay(attempt)
                    
                    logger.warning(
                        f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    if on_retry:
                        on_retry(attempt, delay, e)
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )
                        raise
                    
                    delay = config.calculate_delay(attempt)
                    
                    logger.warning(
                        f"Attempt {attempt}/{config.max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    if on_retry:
                        on_retry(attempt, delay, e)
                    
                    time.sleep(delay)
            
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class ErrorLogger:
    """Contextual error logging with detailed information."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path("logs/errors")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.error_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.json"
    
    def log_error(
        self,
        error: Union[Exception, PPCError],
        context: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        """
        Log error with full context for debugging.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            user_message: User-friendly message to display
        """
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "type": type(error).__name__,
            "message": str(error),
            "context": context or {}
        }
        
        if isinstance(error, PPCError):
            error_data.update(error.to_dict())
        
        if user_message:
            error_data["user_message"] = user_message
        
        # Log to file
        with open(self.error_file, 'a') as f:
            json.dump(error_data, f)
            f.write('\n')
        
        # Log to console with appropriate level
        if isinstance(error, PPCError):
            if error.severity == ErrorSeverity.CRITICAL:
                logger.critical(f"{user_message or str(error)}")
            elif error.severity == ErrorSeverity.HIGH:
                logger.error(f"{user_message or str(error)}")
            else:
                logger.warning(f"{user_message or str(error)}")
        else:
            logger.error(f"{user_message or str(error)}")
    
    def get_recent_errors(self, hours: int = 24) -> list:
        """Get errors from the last N hours."""
        recent_errors = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        if self.error_file.exists():
            with open(self.error_file, 'r') as f:
                for line in f:
                    try:
                        error_data = json.loads(line)
                        error_time = datetime.fromisoformat(error_data['timestamp'])
                        if error_time > cutoff_time:
                            recent_errors.append(error_data)
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        return recent_errors


class ProgressTracker:
    """Track progress for partial completion and resume functionality."""
    
    def __init__(self, state_dir: Optional[Path] = None):
        self.state_dir = state_dir or Path(".state")
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def save_progress(
        self,
        task_id: str,
        progress: Dict[str, Any],
        total_items: Optional[int] = None,
        completed_items: Optional[int] = None
    ):
        """
        Save progress state for a task.
        
        Args:
            task_id: Unique identifier for the task
            progress: Current progress data
            total_items: Total number of items to process
            completed_items: Number of items completed
        """
        state_file = self.state_dir / f"{task_id}.json"
        
        state_data = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "progress": progress,
            "total_items": total_items,
            "completed_items": completed_items,
            "percentage": (completed_items / total_items * 100) if total_items else 0
        }
        
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
        
        logger.info(
            f"Progress saved for task {task_id}: "
            f"{completed_items}/{total_items} items completed "
            f"({state_data['percentage']:.1f}%)"
        )
    
    def load_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Load saved progress for a task.
        
        Args:
            task_id: Unique identifier for the task
            
        Returns:
            Saved progress data or None if not found
        """
        state_file = self.state_dir / f"{task_id}.json"
        
        if not state_file.exists():
            return None
        
        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)
            
            logger.info(
                f"Resuming task {task_id} from "
                f"{state_data['completed_items']}/{state_data['total_items']} items "
                f"({state_data['percentage']:.1f}%)"
            )
            
            return state_data
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to load progress for task {task_id}: {e}")
            return None
    
    def clear_progress(self, task_id: str):
        """Clear saved progress for a task."""
        state_file = self.state_dir / f"{task_id}.json"
        if state_file.exists():
            state_file.unlink()
            logger.info(f"Cleared progress for task {task_id}")
    
    def list_resumable_tasks(self) -> list:
        """List all tasks with saved progress."""
        tasks = []
        
        for state_file in self.state_dir.glob("*.json"):
            try:
                with open(state_file, 'r') as f:
                    state_data = json.load(f)
                    tasks.append({
                        "task_id": state_data["task_id"],
                        "timestamp": state_data["timestamp"],
                        "percentage": state_data["percentage"],
                        "completed": state_data["completed_items"],
                        "total": state_data["total_items"]
                    })
            except (json.JSONDecodeError, KeyError):
                continue
        
        return sorted(tasks, key=lambda x: x["timestamp"], reverse=True)


def handle_api_response(response: Dict[str, Any], raise_on_error: bool = True) -> Dict[str, Any]:
    """
    Handle API response and extract data or raise appropriate errors.
    
    Args:
        response: API response dictionary
        raise_on_error: Whether to raise exceptions on error
        
    Returns:
        Extracted data from response
        
    Raises:
        APIError: If API returned an error
        RateLimitError: If rate limit was hit
    """
    if "error" in response:
        error_msg = response["error"].get("message", "Unknown API error")
        error_code = response["error"].get("code", "")
        
        if "rate_limit" in error_msg.lower() or error_code == "RATE_LIMIT":
            retry_after = response["error"].get("retry_after", 60)
            raise RateLimitError(error_msg, retry_after=retry_after)
        
        if raise_on_error:
            raise APIError(error_msg, context=response["error"])
        
        logger.error(f"API error: {error_msg}")
        return {}
    
    return response.get("data", response)


# Global instances for convenience
error_logger = ErrorLogger()
progress_tracker = ProgressTracker()