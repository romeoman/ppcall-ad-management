"""Base API client with async support and retry logic."""

import asyncio
import logging
from typing import Dict, Any, Optional
import aiohttp
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

logger = logging.getLogger(__name__)


class BaseAPIClient:
    """Abstract base API client with async support and retry logic."""

    def __init__(self, max_concurrent: int = 5):
        """Initialize the base API client.
        
        Args:
            max_concurrent: Maximum number of concurrent requests allowed.
        """
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def __aenter__(self):
        """Enter async context manager."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _make_request(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> Dict[str, Any]:
        """Make an HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            url: URL to make the request to
            **kwargs: Additional arguments to pass to the request
            
        Returns:
            Dict containing the JSON response
            
        Raises:
            aiohttp.ClientResponseError: If the response status is not successful
            aiohttp.ContentTypeError: If the response is not JSON
        """
        if not self.session:
            raise RuntimeError("Client must be used within async context manager")
        
        async with self.semaphore:
            logger.debug(f"Making {method} request to {url}")
            
            async with self.session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                
                # Check if response is JSON
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type:
                    raise aiohttp.ContentTypeError(
                        request_info=response.request_info,
                        history=response.history,
                        message=f"Expected JSON response, got {content_type}"
                    )
                
                return await response.json()