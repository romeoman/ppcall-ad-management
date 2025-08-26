"""DataForSEO API client with async support."""

import aiohttp
from typing import Dict, Any, List, Optional
import logging

from api_integration.base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class DataForSEOClient(BaseAPIClient):
    """DataForSEO API client for keyword research and SERP data."""
    
    def __init__(self, username: str, password: str, max_concurrent: int = 5):
        """Initialize DataForSEO client.
        
        Args:
            username: DataForSEO API username
            password: DataForSEO API password  
            max_concurrent: Maximum concurrent requests
        """
        super().__init__(max_concurrent)
        self.username = username
        self.password = password
        self.base_url = "https://api.dataforseo.com/v3"
        self.auth = aiohttp.BasicAuth(username, password)
    
    async def get_keyword_data(
        self,
        keywords: List[str],
        location_code: int = 2840,  # US by default
        language_code: str = "en"
    ) -> Dict[str, Any]:
        """Get keyword data including search volume and competition.
        
        Args:
            keywords: List of keywords to analyze
            location_code: DataForSEO location code
            language_code: Language code (e.g., "en")
            
        Returns:
            Dict containing keyword data with search volumes
        """
        endpoint = f"{self.base_url}/keywords_data/google_ads/search_volume/live"
        
        payload = [{
            "keywords": keywords,
            "location_code": location_code,
            "language_code": language_code
        }]
        
        return await self._make_request(
            "POST",
            endpoint,
            json=payload,
            auth=self.auth
        )
    
    async def get_keyword_suggestions(
        self,
        keyword: str,
        location_code: int = 2840,
        language_code: str = "en",
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get keyword suggestions based on a seed keyword.
        
        Args:
            keyword: Seed keyword for suggestions
            location_code: DataForSEO location code
            language_code: Language code
            limit: Maximum number of suggestions
            
        Returns:
            Dict containing keyword suggestions with metrics
        """
        endpoint = f"{self.base_url}/keywords_data/google_ads/keywords_for_keywords/live"
        
        payload = [{
            "keywords": [keyword],
            "location_code": location_code,
            "language_code": language_code,
            "limit": limit
        }]
        
        return await self._make_request(
            "POST",
            endpoint,
            json=payload,
            auth=self.auth
        )
    
    async def get_locations(self) -> Dict[str, Any]:
        """Get list of supported locations.
        
        Returns:
            Dict containing available locations with codes
        """
        endpoint = f"{self.base_url}/keywords_data/google_ads/locations"
        
        return await self._make_request(
            "GET",
            endpoint,
            auth=self.auth
        )
    
    async def get_languages(self) -> Dict[str, Any]:
        """Get list of supported languages.
        
        Returns:
            Dict containing available languages with codes
        """
        endpoint = f"{self.base_url}/keywords_data/google_ads/languages"
        
        return await self._make_request(
            "GET",
            endpoint,
            auth=self.auth
        )
    
    async def get_search_volume_history(
        self,
        keywords: List[str],
        location_code: int = 2840,
        language_code: str = "en",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get historical search volume data for keywords.
        
        Args:
            keywords: List of keywords
            location_code: DataForSEO location code
            language_code: Language code
            date_from: Start date (YYYY-MM-DD format)
            date_to: End date (YYYY-MM-DD format)
            
        Returns:
            Dict containing historical search volume data
        """
        endpoint = f"{self.base_url}/keywords_data/google_ads/search_volume/history/live"
        
        payload = [{
            "keywords": keywords,
            "location_code": location_code,
            "language_code": language_code
        }]
        
        if date_from:
            payload[0]["date_from"] = date_from
        if date_to:
            payload[0]["date_to"] = date_to
        
        return await self._make_request(
            "POST",
            endpoint,
            json=payload,
            auth=self.auth
        )
    
    async def get_keyword_metrics_for_site(
        self,
        target: str,
        location_code: int = 2840,
        language_code: str = "en",
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get keyword metrics for a specific website/URL.
        
        Args:
            target: Website URL or domain
            location_code: DataForSEO location code
            language_code: Language code
            limit: Maximum number of keywords
            
        Returns:
            Dict containing keywords for the target site
        """
        endpoint = f"{self.base_url}/keywords_data/google_ads/keywords_for_site/live"
        
        payload = [{
            "target": target,
            "location_code": location_code,
            "language_code": language_code,
            "limit": limit
        }]
        
        return await self._make_request(
            "POST",
            endpoint,
            json=payload,
            auth=self.auth
        )