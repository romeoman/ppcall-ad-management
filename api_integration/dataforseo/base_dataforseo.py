"""Base DataForSEO client with shared authentication and configuration for PPC focus."""

import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
from ..base_client import BaseAPIClient


class BaseDataForSEOClient(BaseAPIClient):
    """
    Base client for DataForSEO API with shared authentication.
    Provides common functionality for both Google Ads and Bing Ads clients.
    """
    
    BASE_URL = "https://api.dataforseo.com/v3"
    
    def __init__(self, login: str, password: str, max_concurrent: int = 5):
        """
        Initialize DataForSEO base client with authentication.
        
        Args:
            login: DataForSEO account login
            password: DataForSEO account password
            max_concurrent: Maximum concurrent API requests (default: 5)
        """
        super().__init__(max_concurrent)
        self.login = login
        self.password = password
        self.auth = None
    
    async def __aenter__(self):
        """Set up session with basic authentication."""
        await super().__aenter__()
        if self.session:
            # Set up basic auth for DataForSEO
            self.auth = aiohttp.BasicAuth(self.login, self.password)
        return self
    
    async def _make_dataforseo_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make authenticated request to DataForSEO API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            payload: Request payload (list of task objects for DataForSEO)
            **kwargs: Additional request parameters
            
        Returns:
            API response as dictionary
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        # DataForSEO expects payload as a list
        if payload is not None and not isinstance(payload, list):
            payload = [payload]
        
        # Use the retry-enabled base request with auth
        return await self._make_request(
            method=method,
            url=url,
            json=payload,
            auth=self.auth,
            **kwargs
        )
    
    async def get_locations(self, country: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get supported locations for targeting.
        
        Args:
            country: Optional country code filter
            
        Returns:
            List of supported locations with codes
        """
        # This will be overridden by platform-specific implementations
        raise NotImplementedError("Subclasses must implement get_locations")
    
    async def get_languages(self) -> List[Dict[str, Any]]:
        """
        Get supported languages for targeting.
        
        Returns:
            List of supported languages with codes
        """
        # This will be overridden by platform-specific implementations
        raise NotImplementedError("Subclasses must implement get_languages")
    
    def format_location_code(self, location_code: int) -> int:
        """
        Format and validate location code.
        
        Args:
            location_code: Location code (e.g., 2840 for USA)
            
        Returns:
            Validated location code
        """
        # DataForSEO uses numeric location codes
        # 2840 = United States (most common default)
        return location_code if location_code else 2840
    
    def format_language_code(self, language_code: str) -> str:
        """
        Format and validate language code.
        
        Args:
            language_code: Language code (e.g., "en" for English)
            
        Returns:
            Validated language code
        """
        # DataForSEO uses ISO 639-1 language codes
        return language_code if language_code else "en"
    
    async def validate_credentials(self) -> bool:
        """
        Validate DataForSEO credentials by making a test request.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            # Use the user info endpoint to validate credentials
            response = await self._make_dataforseo_request(
                method="GET",
                endpoint="appendix/user_data"
            )
            return response.get("status_code") == 20000
        except Exception:
            return False
    
    def build_task_payload(
        self,
        keywords: List[str],
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build a standard task payload for DataForSEO requests.
        
        Args:
            keywords: List of keywords to process
            location_code: Target location code
            language_code: Target language code
            **kwargs: Additional task parameters
            
        Returns:
            Formatted task payload
        """
        task = {
            "keywords": keywords if isinstance(keywords, list) else [keywords],
            "location_code": self.format_location_code(location_code),
            "language_code": self.format_language_code(language_code)
        }
        
        # Add any additional parameters
        task.update(kwargs)
        
        return task
    
    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse DataForSEO response and extract relevant data.
        
        Args:
            response: Raw API response
            
        Returns:
            Parsed response with extracted data
        """
        # DataForSEO responses follow a standard structure
        if response.get("status_code") == 20000:
            # Success response
            tasks = response.get("tasks", [])
            if tasks and len(tasks) > 0:
                task = tasks[0]
                if task.get("status_code") == 20000:
                    return {
                        "success": True,
                        "data": task.get("result", []),
                        "cost": task.get("cost", 0),
                        "id": task.get("id")
                    }
                else:
                    return {
                        "success": False,
                        "error": task.get("status_message", "Task failed"),
                        "status_code": task.get("status_code")
                    }
            else:
                return {
                    "success": False,
                    "error": "No tasks in response"
                }
        else:
            return {
                "success": False,
                "error": response.get("status_message", "Request failed"),
                "status_code": response.get("status_code")
            }