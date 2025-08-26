"""Serper.dev API client for Google search and related services."""

import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
from .base_client import BaseAPIClient


class SerperClient(BaseAPIClient):
    """Client for Serper.dev API - fallback to DataForSEO for search results."""
    
    def __init__(self, api_key: str, max_concurrent: int = 5):
        """
        Initialize Serper.dev client.
        
        Args:
            api_key: Serper.dev API key
            max_concurrent: Maximum concurrent requests
        """
        super().__init__(max_concurrent)
        self.api_key = api_key
        self.base_url = "https://google.serper.dev"
    
    async def __aenter__(self):
        """Create session with proper headers."""
        await super().__aenter__()
        if self.session:
            self.session.headers.update({
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            })
        return self
    
    async def search_google(
        self,
        query: str,
        location: Optional[str] = None,
        gl: Optional[str] = None,
        hl: Optional[str] = None,
        num: Optional[int] = None,
        page: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search Google using Serper.dev API.
        
        Args:
            query: Search query
            location: Location for search
            gl: Country code
            hl: Language code
            num: Number of results
            page: Page number
            **kwargs: Additional search parameters
            
        Returns:
            Search results with organic listings
        """
        endpoint = f"{self.base_url}/search"
        
        payload = {
            "q": query
        }
        
        if location:
            payload["location"] = location
        if gl:
            payload["gl"] = gl
        if hl:
            payload["hl"] = hl
        if num:
            payload["num"] = num
        if page:
            payload["page"] = page
            
        # Add any additional parameters
        payload.update(kwargs)
        
        return await self._make_request("POST", endpoint, json=payload)
    
    async def search_images(
        self,
        query: str,
        location: Optional[str] = None,
        gl: Optional[str] = None,
        hl: Optional[str] = None,
        num: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search for images using Serper.dev API.
        
        Args:
            query: Search query
            location: Location for search
            gl: Country code
            hl: Language code
            num: Number of results
            **kwargs: Additional parameters
            
        Returns:
            Image search results
        """
        endpoint = f"{self.base_url}/images"
        
        payload = {
            "q": query
        }
        
        if location:
            payload["location"] = location
        if gl:
            payload["gl"] = gl
        if hl:
            payload["hl"] = hl
        if num:
            payload["num"] = num
            
        payload.update(kwargs)
        
        return await self._make_request("POST", endpoint, json=payload)
    
    async def search_news(
        self,
        query: str,
        location: Optional[str] = None,
        gl: Optional[str] = None,
        hl: Optional[str] = None,
        num: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search for news using Serper.dev API.
        
        Args:
            query: Search query
            location: Location for search
            gl: Country code
            hl: Language code
            num: Number of results
            **kwargs: Additional parameters
            
        Returns:
            News search results
        """
        endpoint = f"{self.base_url}/news"
        
        payload = {
            "q": query
        }
        
        if location:
            payload["location"] = location
        if gl:
            payload["gl"] = gl
        if hl:
            payload["hl"] = hl
        if num:
            payload["num"] = num
            
        payload.update(kwargs)
        
        return await self._make_request("POST", endpoint, json=payload)
    
    async def search_places(
        self,
        query: str,
        location: Optional[str] = None,
        gl: Optional[str] = None,
        hl: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search for places using Serper.dev API.
        
        Args:
            query: Search query
            location: Location for search
            gl: Country code
            hl: Language code
            **kwargs: Additional parameters
            
        Returns:
            Places search results
        """
        endpoint = f"{self.base_url}/places"
        
        payload = {
            "q": query
        }
        
        if location:
            payload["location"] = location
        if gl:
            payload["gl"] = gl
        if hl:
            payload["hl"] = hl
            
        payload.update(kwargs)
        
        return await self._make_request("POST", endpoint, json=payload)
    
    async def get_autocomplete(
        self,
        query: str,
        gl: Optional[str] = None,
        hl: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get autocomplete suggestions for a query.
        
        Args:
            query: Search query
            gl: Country code
            hl: Language code
            **kwargs: Additional parameters
            
        Returns:
            Autocomplete suggestions
        """
        endpoint = f"{self.base_url}/autocomplete"
        
        payload = {
            "q": query
        }
        
        if gl:
            payload["gl"] = gl
        if hl:
            payload["hl"] = hl
            
        payload.update(kwargs)
        
        return await self._make_request("POST", endpoint, json=payload)