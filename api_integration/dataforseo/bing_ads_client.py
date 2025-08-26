"""Bing Ads API client for DataForSEO - PPC focused implementation."""

from typing import Dict, Any, Optional, List
from .base_dataforseo import BaseDataForSEOClient


class BingAdsClient(BaseDataForSEOClient):
    """
    Bing Ads specific client for DataForSEO API.
    Implements all 10 Bing Ads endpoints for PPC campaigns.
    
    Documentation: https://dataforseo.com/apis/bing-ads-api
    """
    
    async def get_search_volume(
        self,
        keywords: List[str],
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        device: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current search volume data for Bing keywords.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/live/
        
        Args:
            keywords: List of keywords to analyze
            location_code: Target location code
            language_code: Target language code
            device: Device type filter (desktop, mobile, tablet)
            sort_by: Sort results by metric
            
        Returns:
            Monthly search volume and trend data
        """
        endpoint = "keywords_data/bing/search_volume/live"
        
        task = self.build_task_payload(
            keywords=keywords,
            location_code=location_code,
            language_code=language_code
        )
        
        if device:
            task["device"] = device
        if sort_by:
            task["sort_by"] = sort_by
        
        response = await self._make_dataforseo_request(
            method="POST",
            endpoint=endpoint,
            payload=[task]
        )
        
        return self.parse_response(response)
    
    async def get_search_volume_history(
        self,
        keywords: List[str],
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        device: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get historical search volume trends for Bing keywords.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/live/
        
        Args:
            keywords: List of keywords
            location_code: Target location code
            language_code: Target language code
            date_from: Start date for history (YYYY-MM-DD)
            date_to: End date for history (YYYY-MM-DD)
            device: Device type filter
            
        Returns:
            Historical search volume data (12+ months)
        """
        endpoint = "keywords_data/bing/search_volume_history/live"
        
        task = self.build_task_payload(
            keywords=keywords,
            location_code=location_code,
            language_code=language_code
        )
        
        if date_from:
            task["date_from"] = date_from
        if date_to:
            task["date_to"] = date_to
        if device:
            task["device"] = device
        
        response = await self._make_dataforseo_request(
            method="POST",
            endpoint=endpoint,
            payload=[task]
        )
        
        return self.parse_response(response)
    
    async def get_keywords_for_site(
        self,
        target: str,
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract keywords for websites on Bing.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/live/
        
        Args:
            target: Website URL to analyze
            location_code: Target location code
            language_code: Target language code
            limit: Number of results
            offset: Pagination offset
            sort_by: Sort results by metric
            
        Returns:
            Relevant keywords with Bing metrics
        """
        endpoint = "keywords_data/bing/keywords_for_site/live"
        
        task = {
            "target": target,
            "location_code": self.format_location_code(location_code),
            "language_code": self.format_language_code(language_code),
            "limit": limit,
            "offset": offset
        }
        
        if sort_by:
            task["sort_by"] = sort_by
        
        response = await self._make_dataforseo_request(
            method="POST",
            endpoint=endpoint,
            payload=[task]
        )
        
        return self.parse_response(response)
    
    async def get_keywords_for_keywords(
        self,
        keywords: List[str],
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        include_seed_keyword: bool = True
    ) -> Dict[str, Any]:
        """
        Generate keyword suggestions on Bing.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/live/
        
        Args:
            keywords: Seed keywords
            location_code: Target location code
            language_code: Target language code
            limit: Number of suggestions
            offset: Pagination offset
            include_seed_keyword: Include original keywords
            
        Returns:
            Bing-specific keyword suggestions
        """
        endpoint = "keywords_data/bing/keywords_for_keywords/live"
        
        task = self.build_task_payload(
            keywords=keywords,
            location_code=location_code,
            language_code=language_code
        )
        
        task.update({
            "limit": limit,
            "offset": offset,
            "include_seed_keyword": include_seed_keyword
        })
        
        response = await self._make_dataforseo_request(
            method="POST",
            endpoint=endpoint,
            payload=[task]
        )
        
        return self.parse_response(response)
    
    async def get_keyword_performance(
        self,
        keywords: List[str],
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        match: str = "exact"
    ) -> Dict[str, Any]:
        """
        Get device-specific performance metrics for keywords.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/live/
        
        Args:
            keywords: Keywords to analyze
            location_code: Target location code
            language_code: Target language code
            match: Match type (exact, phrase, broad)
            
        Returns:
            Performance metrics by device:
            - CTR by device type
            - Impressions by device
            - Position data
            - Device distribution
        """
        endpoint = "keywords_data/bing/keyword_performance/live"
        
        task = self.build_task_payload(
            keywords=keywords,
            location_code=location_code,
            language_code=language_code
        )
        
        task["match"] = match
        
        response = await self._make_dataforseo_request(
            method="POST",
            endpoint=endpoint,
            payload=[task]
        )
        
        return self.parse_response(response)
    
    async def get_keyword_suggestions_for_url(
        self,
        target: str,
        language_code: Optional[str] = None,
        exclude_brands: bool = False,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        AI-powered keyword suggestions from landing page analysis.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/live/
        
        Args:
            target: URL to analyze
            language_code: Target language code
            exclude_brands: Exclude brand keywords
            limit: Number of suggestions
            
        Returns:
            AI-generated contextual keywords with confidence scores
        """
        endpoint = "keywords_data/bing/keyword_suggestions_for_url/live"
        
        task = {
            "target": target,
            "language_code": self.format_language_code(language_code),
            "exclude_brands": exclude_brands,
            "limit": limit
        }
        
        response = await self._make_dataforseo_request(
            method="POST",
            endpoint=endpoint,
            payload=[task]
        )
        
        return self.parse_response(response)
    
    async def get_audience_estimation(
        self,
        keywords: List[str],
        location_code: Optional[int] = None,
        language_code: Optional[str] = None,
        bid: Optional[float] = None,
        match: str = "exact",
        daily_budget: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Estimate audience size and demographics for campaigns.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/live/
        
        Args:
            keywords: Campaign keywords
            location_code: Target location code
            language_code: Target language code
            bid: Max CPC bid
            match: Match type
            daily_budget: Daily campaign budget
            
        Returns:
            Audience estimates:
            - Size and reach
            - Demographics (age, gender)
            - Geographic distribution
            - Device usage patterns
        """
        endpoint = "keywords_data/bing/audience_estimation/live"
        
        task = self.build_task_payload(
            keywords=keywords,
            location_code=location_code,
            language_code=language_code
        )
        
        task["match"] = match
        
        if bid is not None:
            task["bid"] = bid
        if daily_budget is not None:
            task["daily_budget"] = daily_budget
        
        response = await self._make_dataforseo_request(
            method="POST",
            endpoint=endpoint,
            payload=[task]
        )
        
        return self.parse_response(response)
    
    async def get_overview(self) -> Dict[str, Any]:
        """
        Get Bing Ads API capabilities overview.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/bing/overview/
        
        Returns:
            API capabilities and metadata
        """
        endpoint = "keywords_data/bing/overview"
        
        response = await self._make_dataforseo_request(
            method="GET",
            endpoint=endpoint
        )
        
        return self.parse_response(response)
    
    async def get_locations(self, country: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get supported Bing locations.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/bing/locations/
        
        Args:
            country: Optional country code filter
            
        Returns:
            List of supported locations
        """
        endpoint = "keywords_data/bing/locations"
        
        if country:
            endpoint = f"{endpoint}/{country}"
        
        response = await self._make_dataforseo_request(
            method="GET",
            endpoint=endpoint
        )
        
        return self.parse_response(response)
    
    async def get_languages(self) -> List[Dict[str, Any]]:
        """
        Get supported Bing languages.
        
        Documentation: https://docs.dataforseo.com/v3/keywords_data/bing/languages/
        
        Returns:
            List of supported languages
        """
        endpoint = "keywords_data/bing/languages"
        
        response = await self._make_dataforseo_request(
            method="GET",
            endpoint=endpoint
        )
        
        return self.parse_response(response)
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get Bing Ads categories for keyword research.
        
        Returns:
            List of available categories
        """
        endpoint = "keywords_data/bing/categories"
        
        response = await self._make_dataforseo_request(
            method="GET",
            endpoint=endpoint
        )
        
        return self.parse_response(response)